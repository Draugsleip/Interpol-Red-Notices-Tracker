import os, time, pika ,requests ,json
from dotenv import load_dotenv

from Organizer.minio_client import MinioClient
from Organizer.database_config import db_init, Notice, LocalSession

class Organizer:
    def __init__(self):
        load_dotenv()
        self.queue_name = os.getenv("RABBITMQ_DEFAULT_QUEUE_NAME")
        self.connection = None
        self.channel = None

        self.minio = MinioClient()

        db_init()
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
                heartbeat=600,  # send heartbeat to prevent conn from to getting closed
                blocked_connection_timeout=9999,  # timeout after that amount if blocked
                connection_attempts=360,
                retry_delay=10
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True) # thanks to "durable" you are not losing
            print(f"Rabbit connection (download) established successfully!") # any message in case of restarting rabbit

        except Exception as e:
            print(f"Rabbit connection (download) failed: {e}")
            raise

    def _ensure_connect(self):
        try:
            if self.connection is None or self.connection.is_closed:
                print("Connection (download) lost, will try to reconnect...")
                self._connect()
        except Exception as e:
            print(f"Error during _ensure_connect (download): {e}, attempting full reconnect...")
            self._connect()

    def save_to_db(self, notice_data):
        db = LocalSession()

        # here im trying to see if there is any existing notices before saving them
        # and if there is any --> update them with the latest values

        try:
            existing_notice = db.query(Notice).filter(Notice.entity_id==notice_data.get("entity_id")).first()
            if existing_notice:
                is_notice_changed = False
                for key, value in notice_data.items():
                    if hasattr(existing_notice, key):
                        if getattr(existing_notice, key) != value:
                            setattr(existing_notice, key, value)
                            is_notice_changed = True
                if is_notice_changed:
                    db.commit()
                    print(f"UPDATED notice: '{notice_data.get('entity_id')}'")
            else:
                new_notice = Notice(**notice_data)
                db.add(new_notice)
                db.commit()
                print(f"NEW notice: '{new_notice.entity_id}'")


        except Exception as e:
            db.rollback()
            print(f"Error saving to db: {e}")
            raise
        finally:
            db.close()

    def process_rabbit_messages(self, ch, method, properties, body):
        # properties ==> message metadata: headers, content type etc...

        try:
            notice_data = json.loads(body.decode("utf-8"))
            print(f"Message received from rabbit for: {notice_data.get('entity_id')}")

            # rabbit.details -> db
            self.save_to_db(notice_data)

            # api.imgs -> minio
            entity_id = notice_data.get("entity_id")
            img_urls =self._get_img_urls(notice_data.get("imgs_link"))
            if img_urls:
                for idx, img_url in enumerate(img_urls, start=1):

                    minio_obj_name = f"{entity_id}/image_{idx}.png"
                    result = self.minio.send_to_minio_img(url=img_url, object_name=minio_obj_name)
                    if result:
                        pass
                    else:
                        print(f"{minio_obj_name} failed to send img to minio")
            else:
                print(f"No imgs found for entity_id: {entity_id}")

            # delete the message from the queue after its received
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            print(f"Error decoding json: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"Error processing message: {e}")

            # requeue the message in case of a temporary failure
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def consume_start(self):
        while True:
            try:
                self._ensure_connect()
                # default=1 message at a time
                self.channel.basic_qos(prefetch_count=75)

                # start receiving messages and send it to processing (save to db)
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.process_rabbit_messages,
                )

                self.channel.start_consuming()

            except KeyboardInterrupt:
                print("Organizer stopped by user!")
                self.channel.stop_consuming()
                self.connection.close()
            except Exception as e:
                print(f"Error consuming message: {e}")
                time.sleep(3)
                continue

    def _get_img_urls(self, imgs_link:str) -> list:
        try:
            with open("config/headers.json") as f:
                headers = json.load(f)

            response = requests.get(imgs_link, headers=headers, timeout=10)
            response.raise_for_status()

            sub_imgs = response.json()
            imgs_cluster = sub_imgs.get("_embedded", {}).get("images", [])

            img_urls = []
            for img in imgs_cluster:
                hrefs = img.get("_links", {}).get("self", {}).get("href")
                if hrefs:
                    img_urls.append(hrefs)
            return img_urls

        except Exception as e:
            print(f"Error getting image from url: {imgs_link} -> {e}")
            return []

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Error closing the rabbitmq connection: {e}")

def mr_start():
    organizer = Organizer()
    organizer.consume_start()

if __name__ == "__main__":
    mr_start()
