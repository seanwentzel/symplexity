import abc
from functools import cached_property

from symplexity import api
from symplexity.basic_types import Direction

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

    @cached_property
    @abc.abstractmethod
    def position(self) -> float:
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

    def __repr__(self) -> str:
        return f"ApiMarket({self.base.url})"

    @staticmethod
    def from_id(id) -> "ApiMarket":
        return ApiMarket(api.wrapper.market(id))

    def p(self) -> float:
        return self.base.p

    def y(self):
        return self.base.pool["YES"]

    def n(self):
        return self.base.pool["NO"]

    @cached_property
    def position(self) -> float:
        pos = api.wrapper.get_position(api.wrapper.me.id, self.base.id)
        y = pos["YES"] if "YES" in pos else 0
        n = pos["NO"] if "NO" in pos else 0
        return y - n

    def total_liquidity(self):
        return self.base.totalLiquidity

    def inverse(self) -> "InverseMarket":
        return InverseMarket(self)

    def latest(self) -> "ApiMarket":
        """
        Fetch a fresh copy of this market. Useful for validating that your trades are still profitable.
        """
        return ApiMarket(api.wrapper.market(self.base.id))


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

    @property
    def position(self) -> float:
        return -self.base.position

    def inverse(self) -> ApiMarket:
        return self.base
