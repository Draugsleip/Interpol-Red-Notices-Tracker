import os
import string
from urllib.parse import urlencode, quote
from dotenv import load_dotenv
import requests

class QueryOptions:

    def __init__(self):
        load_dotenv()
        self.API_BASE_URL = os.getenv("API_URL")

    def build_url(self, params: dict | str |None = None, result_per_page: int = 200):
        if params is None:
            return f"{self.API_BASE_URL}?resultPerPage={result_per_page}"
        if isinstance(params, str):
            encoded = quote(params, safe="")
            return f"{self.API_BASE_URL}/{encoded}"
        return f"{self.API_BASE_URL}?{urlencode(params)}&resultPerPage={result_per_page}"

    def bruteforce_params(self, light_countries, heavy_countries, session: requests.Session):
        ages = list(range(121))
        genders = ["M", "F", "U"]

        chars_list = list(string.ascii_lowercase)
        chars_list.append("null")

        for nation in light_countries:
            yield {"nationality": nation}

        for nation in heavy_countries:
            for age in ages:
                for gender in genders:
                    base_params = {
                        "nationality": nation,
                        "ageMin": age,
                        "ageMax": age,
                        "sexId": gender
                    }

                    try:
                        check_url = self.build_url(base_params)
                        response = session.get(check_url, timeout=10)
                        response.raise_for_status()
                        heavy_data = response.json()
                        total = heavy_data.get("total", 0)

                        if total > 160:
                            for char in chars_list:
                                yield {
                                    **base_params,
                                    "forename": char
                                }
                                yield {
                                    **base_params,
                                    "name": char
                                }
                                yield {
                                    **base_params,
                                    "freeText": char
                                }
                            continue
                    except Exception as e:
                        print(f"Total > 160 check failed: {e}")
                    yield base_params

            for char in chars_list:
                for gender in genders:
                    yield {
                        "nationality": nation,
                        "sexId": gender
                    }

                    yield {
                        "nationality": nation,
                        "sexId": gender,
                        "name": char
                    }

                    yield {
                        "nationality": nation,
                        "sexId": gender,
                        "forename": char
                    }

                    yield {
                        "nationality": nation,
                        "sexId": gender,
                        "freeText": char
                    }

        # for null nationality
        for age in ages:
            for gender in genders:
                yield {
                    "ageMin": age,
                    "ageMax": age,
                    "sexId": gender
                }

        # for null gender
        for age in ages:
            yield {
                "ageMin": age,
                "ageMax": age,
            }

        # null nationality, null gernder
        for gender in genders:
            yield {
                "sexId": gender
            }

        yield {}

    def bruteforce_urls(self, light_countries, heavy_countries, session):
        for params in self.bruteforce_params(light_countries, heavy_countries, session):
            yield self.build_url(params)