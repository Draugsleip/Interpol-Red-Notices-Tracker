import pika, os, dotenv, json, time

class RabbitClient:

    def __init__(self, queue_name: str = "notices_meta"):
        dotenv.load_dotenv()

        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self._connect()
    def _connect(self):
        try:
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                except:
                    pass

            creds = pika.PlainCredentials(
                username=os.getenv("RABBITMQ_DEFAULT_USER"),
                password=os.getenv("RABBITMQ_DEFAULT_PASS")
            )

            parameters = pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_DEFAULT_HOST", "rabbitmq"),
                virtual_host=os.getenv("RABBITMQ_DEFAULT_VHOST", "/"),
                credentials=creds,
                heartbeat=60, # send heartbeat to prevent conn from get closed
                blocked_connection_timeout=300, # timeout after that amount if blocked
                connection_attempts=360,
                retry_delay=10
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            print(f"Rabbit connection (upload) established successfully!")
            return

        except Exception as e:
            print(f"Rabbit connection (upload) failed: {e}")
            raise

    def _ensure_connect(self):
        try:
            # conn check
            if self.connection is None or self.connection.is_closed:
                print("Connection (upload) lost, will try to reconnect...")
                self._connect()
                return

            # channel check
            if self.channel is None or self.channel.is_closed:
                print(f"Channel (upload) is lost, recreating channel...")
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
        except Exception as e:
            print(f"Error during _ensure_connect (upload): {e}, attempting full reconnect...")
            self._connect()

    def publish_meta(self, meta: dict):
        body = json.dumps(meta, ensure_ascii=False)

        self._ensure_connect()

        max_retries = 10

        for attempt in range(max_retries):
            try:
                self.channel.basic_publish(
                    exchange="",
                    routing_key=self.queue_name,
                    body=body.encode('utf-8'),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type="application/json"
                    )
                )
                return

            except (pika.exceptions.ConnectionClosed,
                    pika.exceptions.ChannelClosed,
                    pika.exceptions.StreamLostError,
                    ConnectionAbortedError) as e:
                if attempt < max_retries - 1:
                    print(f"Reconnecting to rabbit...")
                    self._connect()
                else:
                    print(f"Failed to publish after {max_retries} attempts: {e}")
                    raise

            except Exception as e:
                print(f"Unexpected error during rabbit publish: {e}")
                raise

    def close(self):
        try:
            self.connection.close()
        except Exception as e:
            pass
