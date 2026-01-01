import json
import os
import requests
import time
from datetime import datetime
import pycountry

from dotenv import load_dotenv
from minio import S3Error

from Producer.query_options import QueryOptions
from Producer.rabbitmq_client import RabbitClient

class Producer:
    def __init__(self):
        load_dotenv()

        self.API_BASE_URL = os.getenv("API_URL")
        self.API_RATE_DELAY = os.getenv("API_RATE_LIMIT_DELAY")
        self.POLL_INTERVAL_SECONDS = os.getenv("POLL_INTERVAL_SECONDS")

        self.query_options = QueryOptions()
        self.rabbit= RabbitClient(queue_name=os.getenv("RABBITMQ_DEFAULT_QUEUE_NAME", "notices_meta"))

    def make_session(self):
        with open("config/headers.json") as f:
            headers = json.load(f)

        sess = requests.Session()
        sess.headers.update(headers)
        return sess

    def _get_page_json(self, session, url: str) -> dict:
        response = session.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_all_data(self) -> list | None:
        all_notices = []
        session = self.make_session()

        try:
            light_countries, heavy_countries = self._classify_countries(session)

            print("Lights:", light_countries)
            print("Heavies:", heavy_countries)

            for urls in self.query_options.bruteforce_urls(light_countries, heavy_countries, session):
                notices = self._fetch_notices_for_url(session, urls)
                all_notices.extend(notices)

                try:
                    if self.rabbit.connection and not self.rabbit.connection.is_closed:
                        self.rabbit.connection.process_data_events(time_limit=0.1)
                except:
                    pass

            unique_only = {}

            # check if a notice is already exists
            for notice in all_notices:
                notice_id = (notice.get("entity_id")
                        or notice.get("_links", {}).get("self", {}).get("href")
                )
                if notice_id:
                    unique_only[notice_id] = notice

            notice_details = {}

            for unique_notice in unique_only.values():
                notice_id = unique_notice.get("entity_id")
                if not notice_id:
                    continue

                try:
                    notice_detail = self.fetch_details(notice_id, session)
                    notice_details[notice_id] = notice_detail

                    notice_meta = {
                        "date_of_birth":notice_details[notice_id].get("date_of_birth"),
                        "distinguishing_marks":notice_details[notice_id].get("distinguishing_marks"),
                        "weight":notice_details[notice_id].get("weight"),
                        "nationalities": notice_details[notice_id].get("nationalities"),
                        "entity_id": notice_id,
                        "eyes_colors_id": notice_details[notice_id].get("eyes_colors_id"),
                        "sex_id":notice_details[notice_id].get("sex_id"),
                        "place_of_birth":notice_details[notice_id].get("place_of_birth"),
                        "forename":notice_details[notice_id].get("forename"),
                        "arrest_warrants":notice_details[notice_id].get("arrest_warrants"),
                        "country_of_birth_id":notice_details[notice_id].get("country_of_birth_id"),
                        "hairs_id":notice_details[notice_id].get("hairs_id"),
                        "name":notice_details[notice_id].get("name"),
                        "languages_spoken_ids":notice_details[notice_id].get("languages_spoken_ids"),
                        "height":notice_details[notice_id].get("height"),

                        "imgs_link":notice_details[notice_id].get("_links", {}).get("images", {}).get("href") if notice_details[notice_id].get("_links") else None,

                        "upload_time": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    }

                    try:
                        # send notice meta to rabbit
                        self.rabbit.publish_meta(notice_meta)

                    except Exception as e:
                        print(f"Rabbit upload error for {notice_id} -> {e}")

                except S3Error as e:
                    print(f"Something went wrong with the minio upload: {e}")

                except Exception as e:
                    print(f"Error for {notice_id}: {e}")

            # with open("notice_details.json", "w", encoding="utf-8") as f:
            #     f.write(json.dumps(notice_details, indent=3, ensure_ascii=False))

            print("Raw count:", len(all_notices))
            # with open("raw_output.json", "w") as f:
            #     f.write(json.dumps(all_notices, indent=3, ensure_ascii=False))

            print("Unique count:", len(unique_only))
            return list(unique_only.values())

        except Exception as e:
            print(f"Something went wrong: {e}")
            return []
        finally:
            self.rabbit.close()

    def _fetch_notices_for_url(self, session, url):
        notices = []
        while url:
            data = self._get_page_json(session, url)
            notices.extend(data.get("_embedded", {}).get("notices", []))
            url = data.get("_links", {}).get("next", {}).get("href")
        return notices

    def _classify_countries(self, session):
        # classify the country as either light or heavy in order to its "total" count
        # total < 160 -> lights
        # total > 160 -> heavies
        standard_countries = [country.alpha_2 for country in pycountry.countries]
        non_standard_countries = ["UNK", "XK", "914", "922", "916"]
        all_countries = list(set(standard_countries + non_standard_countries))

        light = []
        heavy = []

        for country in all_countries:
            url = self.query_options.build_url({"nationality": country})
            data = self._get_page_json(session, url)

            total = data.get("total")

            if total is None:
                light.append(country)
            elif total <= 160:
                light.append(country)
            else:
                heavy.append(country)
        return light, heavy

    def fetch_details(self, notice_id, session):
        url = self.query_options.build_url(notice_id)
        details_data = self._get_page_json(session, url)

        return details_data

    def continuous_run(self):
        interval_seconds = self.POLL_INTERVAL_SECONDS

        while True:
            start = time.time()
            self.fetch_all_data()
            elapsed = time.time() - start
            sleep_for = max(float(interval_seconds) - elapsed, 0)
            print(f"Fetch cycle finished in {round(elapsed/60)} minutes, sleeping for {round(sleep_for/60)} minutes")
            time.sleep(sleep_for)

if __name__ == "__main__":
    producer = Producer()
    producer.continuous_run()
