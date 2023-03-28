import config

import json
import requests
import manifoldpy.api as api

BASE_URI = "https://manifold.markets/api/v0"

def get_position(me, market):
    # untested
    response = requests.get(
        f"{BASE_URI}/market/{market.id}/positions?userId={me['id']}"
    )
    return response

def parse(response) -> dict:
    return json.loads(response.text)

def initialize() -> tuple[api.APIWrapper, dict]:
    api_key = config.load()["api_key"]

    wrapper = api.APIWrapper(api_key)
    me = parse(wrapper.me())
    return (wrapper, me)