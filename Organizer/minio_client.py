import os
import json
import io
from minio import Minio, S3Error
import dotenv
import requests

class MinioClient:

    def __init__(self):
        dotenv.load_dotenv()

        minio_host = os.getenv("MINIO_HOST", "minio")
        minio_port = os.getenv("MINIO_PORT", "9000")
        endpoint = f"{minio_host}:{minio_port}"

        self.minio_client = Minio(endpoint,
                                  access_key=os.getenv("MINIO_ROOT_USER"),
                                  secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
                                  secure=False
                                  )

        self.bucket = os.getenv("MINIO_BUCKET", "notice-details")
        self._ensure_bucket_exists()

        # session is faster than doing request.get() for each individual item
        # because it uses the same tcp for every item rather than creating a brand new everytime
        self.session = requests.Session()
        try:
            with open("config/headers.json") as f:
                self.session.headers.update(json.load(f))
        except Exception as e:
            print(f"Error with creating a session (minio_client): {e}")

    def _ensure_bucket_exists(self):
        # to make sure minio bucket exists
        try:
            if not self.minio_client.bucket_exists(self.bucket):
                self.minio_client.make_bucket(self.bucket)
                print(f"Bucket {self.bucket} created")
        except Exception as e:
            print(f"Error with bucket: {e}")

    def send_to_minio_img(self, url:str, object_name:str):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            img_bytes = response.content
            img_io = io.BytesIO(img_bytes)

            self.minio_client.put_object(
                self.bucket,
                object_name,
                img_io,
                length=len(img_bytes),
                content_type="image/png"
            )
            # print(f"Saved img details to {self.bucket} successfully!")
            return f"{self.bucket}/{object_name}"
        except S3Error as e:
            print(f"Error with bucket: {e}")
            return None
        except Exception as e:
            print(f"Error uploading imgs: {e}")
            return None

    def list_from_minio(self, prefix:str = "") -> list:
        try:
            objects = self.minio_client.list_objects(self.bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []

    def get_image(self, object_name: str) -> bytes:
        try:
            response = self.minio_client.get_object(self.bucket, object_name)
            image_bytes = response.read()
            response.close()
            response.release_conn()
            return image_bytes
        except S3Error as e:
            print(f"Error retrieving image {object_name}: {e}")
            return None
        except Exception as e:
            print(f"Error getting image: {e}")
            return None