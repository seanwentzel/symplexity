import config

import json
import requests
import manifoldpy.api as api

BASE_URI = "https://manifold.markets/api/v0"


def get_position(me: dict, market: api.Market) -> float:
    """
    Experimental.
    Returns a positive number of shares for `YES` positions, and a negative number for `NO` positions.
    """
    response = requests.get(
        f"{BASE_URI}/market/{market.id}/positions?userId={me['id']}"
    )
    posns = parse(response)
    assert len(posns) <= 1
    if len(posns) == 0:
        return 0
    pos = posns[0]["totalShares"]
    y = pos["YES"] if "YES" in pos else 0
    n = pos["NO"] if "NO" in pos else 0
    return y - n


def parse(response) -> dict:
    return json.loads(response.text)


def initialize() -> tuple[api.APIWrapper, dict]:
    api_key = config.load_config()["api_key"]

    wrapper = api.APIWrapper(api_key)
    me = parse(wrapper.me())
    return (wrapper, me)


def slug_to_id(slug: str):
    return api.get_slug(slug).id


def create_test_market(wrapper: api.APIWrapper, nonce: str='') -> str:
    response = wrapper.create_market(outcomeType="BINARY",question=f"test market {nonce}, resolves N/A", description="just testing", closeTime=1839236868000, visibility="unlisted", initialProb=50)
    return parse(response.text)["id"]