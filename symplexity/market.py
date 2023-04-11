import abc
import manifoldpy.api as api

from api import get_position
from basic_types import Direction

MECHANISM = "cpmm-1"


def raw_prob(p, y, n):
    return p * n / ((1 - p) * y + p * n)


class VirtualMarket(metaclass=abc.ABCMeta):
    """
    A `VirtualMarket` represents a market which obeys the Maniswap protocol.
    This can be an actual market on Manifold, but it can be useful to make
    hypothetical markets to simplify computation too.
    """

    @abc.abstractmethod
    def p(self) -> float:
        pass

    @abc.abstractmethod
    def y(self) -> float:
        pass

    @abc.abstractmethod
    def n(self) -> float:
        pass

    @abc.abstractmethod
    def get_position(self, user) -> float:
        pass

    def prob(self) -> float:
        return raw_prob(self.p(), self.y(), self.n())

    def c(self) -> float:
        """The market constant"""
        p = self.p()
        return self.y() ** p * self.n() ** (1 - p)

    def invest_effect(self, inv: float) -> tuple[float, float]:
        """
        The effect of investing `inv` mana yes.

        Returns: (number of YES shares bought, new implied probability)
        """
        p = self.p()
        y_2 = self.y() + inv
        n_2 = self.n() + inv
        y_t = (self.c() / (n_2) ** (1 - p)) ** (1.0 / p)
        return y_2 - y_t, raw_prob(p, y_t, n_2)

    @abc.abstractmethod
    def inverse(self) -> "VirtualMarket":
        pass

    @staticmethod
    def from_direction(direction: Direction) -> "VirtualMarket":
        base_market = ApiMarket.from_id(direction.id)
        if direction.outcome == "YES":
            return base_market
        else:
            return InverseMarket(base_market)


class ApiMarket(VirtualMarket):
    """
    A market actually backed by the Manifold API.
    """

    base: api.Market

    def __init__(self, base) -> None:
        super().__init__()
        assert base.mechanism == MECHANISM
        self.base = base

    @staticmethod
    def from_slug(slug) -> "ApiMarket":
        return ApiMarket(api.get_slug(slug))

    @staticmethod
    def from_id(id) -> "ApiMarket":
        return ApiMarket(api.get_market(id))

    def p(self):
        return self.base.p

    def y(self):
        return self.base.pool["YES"]

    def n(self):
        return self.base.pool["NO"]

    def get_position(self, user) -> float:
        # xcxc
        return get_position(user, self.base)

    def total_liquidity(self):
        return self.base.totalLiquidity

    def inverse(self) -> "InverseMarket":
        return InverseMarket(self)

    def latest(self) -> "ApiMarket":
        """
        Fetch a fresh copy of this market. Useful for validating that your trades are still profitable.
        """
        return ApiMarket(api.get_market(self.base.id))


class InverseMarket(VirtualMarket):
    """
    A market which resolves YES iff the `base` market resolves NO,
    and with exactly opposite liquidity provision.
    """

    base: ApiMarket

    def __init__(self, base: ApiMarket) -> None:
        super().__init__()
        self.base = base

    def p(self):
        return 1 - self.base.p()

    def y(self):
        return self.base.n()

    def n(self):
        return self.base.y()

    def get_position(self, user) -> float:
        return -self.base.get_position(user)

    def inverse(self) -> ApiMarket:
        return self.base
