from dataclasses import dataclass
import json
import logging
from uuid import uuid4
from dataclasses_json import DataClassJsonMixin
import manifoldpy.api as api
import requests

import symplexity.config as config
from symplexity.basic_types import Outcome

BASE_URI = "https://manifold.markets/api/v0"

logger = logging.getLogger("symplexity.api")

Market = api.Market  # use the `manifoldpy` Market type


@dataclass
class User(DataClassJsonMixin):
    id: str
    balance: float


@dataclass
class ApiError(Exception):
    status: int
    body: str


class Wrapper:
    session: requests.Session
    me: User

    def __init__(self, key) -> None:
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Key {key}"
        self.me = self._me()

    def _request(self, req: requests.Request) -> str:
        req.params["symplexity_cachebuster"] = uuid4()

        response = self.session.send(
            self.session.prepare_request(req), timeout=(3.05, 20)
        )
        if 400 <= response.status_code:
            raise ApiError(response.status_code, response.text)
        return response.text

    def _me(self) -> User:
        req = requests.Request("GET", api.ME_URL)
        return User.from_json(self._request(req))

    def market(self, id) -> api.Market:
        req = requests.Request("GET", api.SINGLE_MARKET_URL.format(id))
        return api.Market.from_json(json.loads(self._request(req)))

    def balance(self) -> float:
        latest_me = self._me()
        return latest_me.balance

    @staticmethod
    def from_config() -> "Wrapper":
        api_key = config.load_config()["api_key"]
        return Wrapper(api_key)

    def get_position(self, user_id: str, market_id: str) -> dict[Outcome, float]:
        """
        Experimental.
        Returns a positive number of shares for `YES` positions, and a negative number for `NO` positions.
        """
        response = requests.get(
            f"{BASE_URI}/market/{market_id}/positions?userId={user_id}"
        )
        posns = parse(response)
        logger.debug(f"got positions for {market_id}")
        logger.debug(posns)
        assert len(posns) <= 1
        if len(posns) == 0:
            return {}

        pos = posns[0]["totalShares"]
        return pos


def parse(response) -> dict:
    return json.loads(response.text)


def initialize() -> tuple[api.APIWrapper, dict]:
    api_key = config.load_config()["api_key"]

    wrapper = api.APIWrapper(api_key)
    me = parse(wrapper.me())
    return (wrapper, me)


def slug_to_id(slug: str):
    return api.get_slug(slug).id


def create_test_market(wrapper: api.APIWrapper, nonce: str = "") -> str:
    response = wrapper.create_market(
        outcomeType="BINARY",
        question=f"test market {nonce}, resolves N/A",
        description="just testing",
        closeTime=1839236868000,
        visibility="unlisted",
        initialProb=50,
    )
    return parse(response)["id"]


wrapper = Wrapper.from_config()
