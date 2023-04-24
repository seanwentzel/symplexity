from dataclasses import dataclass
import json
import logging
from uuid import uuid4
from dataclasses_json import DataClassJsonMixin
import manifoldpy.api as api
import requests

import symplexity.config as config
from symplexity.basic_types import Outcome
import symplexity.rate_limiter as rate_limiter

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
    read_limiter: rate_limiter.LeakyBucket
    write_limiter: rate_limiter.LeakyBucket
    _manifoldpy: api.APIWrapper

    @staticmethod
    def from_config() -> "Wrapper":
        api_key = config.load_config()["api_key"]
        return Wrapper(api_key)

    def __init__(self, key: str, read_only: bool = False) -> None:
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Key {key}"
        if not read_only:
            self._manifoldpy = api.APIWrapper(key)

        # TODO: make these configurable
        self.read_limiter = rate_limiter.LeakyBucket(300, 20)
        self.write_limiter = rate_limiter.LeakyBucket(20, 0.1)

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
        self.read_limiter.block_until_allowed(1)
        return User.from_json(self._request(req))

    def market(self, id) -> api.Market:
        req = requests.Request("GET", api.SINGLE_MARKET_URL.format(id))
        self.read_limiter.block_until_allowed(1)
        return api.Market.from_json(json.loads(self._request(req)))

    def balance(self) -> float:
        latest_me = self._me()
        return latest_me.balance

    def get_position(self, user_id: str, market_id: str) -> dict[Outcome, float]:
        """
        Experimental.
        Returns a positive number of shares for `YES` positions, and a negative number for `NO` positions.
        """

        request = requests.Request(
            "GET", f"{BASE_URI}/market/{market_id}/positions?userId={user_id}"
        )
        self.read_limiter.block_until_allowed(1)
        posns = json.loads(self._request(request))
        logger.debug(f"got positions for {market_id}")
        logger.debug(posns)
        assert len(posns) <= 1
        if len(posns) == 0:
            return {}

        pos = posns[0]["totalShares"]
        return pos

    def lease_writes(self, tokens: int) -> list[rate_limiter.Token]:
        return self.write_limiter.block_until_allowed(tokens)

    def make_bet(
        self, mana: float, market_id: str, outcome: Outcome, token: rate_limiter.Token
    ) -> str:
        token.use()
        response = self._manifoldpy.make_bet(
            amount=mana,
            contractId=market_id,
            outcome=outcome,
        )
        if 400 <= response.status_code:
            raise ApiError(response.status_code, response.text)
        return response.text


def slug_to_id(slug: str):
    return api.get_slug(slug).id


def create_test_market(wrapper: Wrapper, nonce: str = "") -> str:
    response = wrapper._manifoldpy.create_market(
        outcomeType="BINARY",
        question=f"test market {nonce}, resolves N/A",
        description="just testing",
        closeTime=1839236868000,
        visibility="unlisted",
        initialProb=50,
    )
    return json.loads(response.text)["id"]


wrapper = Wrapper.from_config()
