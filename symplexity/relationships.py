import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json

from symplexity.arb import ArbOpportunity, arb
from symplexity.basic_types import Direction, Outcome
from symplexity.market import VirtualMarket
from symplexity.trades import RecommendedTrade

EQUIVALENT_MARGIN = 0.005
ORDERED_MARGIN = 0.02
INF = 2000.0

logger = logging.getLogger("symplexity.relationships")


@dataclass
class Equivalence(DataClassJsonMixin):
    directions: list[Direction]
    margin: float = EQUIVALENT_MARGIN

    def generate_opportunities(self) -> Iterator[list[RecommendedTrade]]:
        """
        First, find positions we can exit out of at a profit.
        Second, find positions we can transfer at a profit.
        Third, find new dutch books.
        """

        def find_opp() -> Optional[list[RecommendedTrade]]:
            markets = [VirtualMarket.from_direction(d) for d in self.directions]
            markets.sort(key=lambda m: m.prob())
            positions = [market.position for market in markets]
            for m, p in zip(markets, positions):
                logger.debug("Looking for opportunities in:")
                logger.debug(f"Market: {m}, Position: {p}, Probability: {m.prob()}")

            # Exit 2-sided positions
            for i in range(len(markets)):
                for j in range(len(markets) - 1, i, -1):
                    max_shares = min(positions[j], -positions[i])
                    attempt = arb(
                        markets=[markets[i], markets[j].inverse()],
                        target=1.0,
                        max_shares=max_shares,
                    )
                    if len(attempt) > 0:
                        return attempt

            # Transfer 1-sided positions
            for i in range(len(markets)):
                for j in range(len(markets) - 1, i, -1):
                    max_shares = max(positions[j], -positions[i])
                    attempt = arb(
                        markets=[markets[i], markets[j].inverse()],
                        target=1.0,
                        max_shares=max_shares,
                    )
                    if len(attempt) > 0:
                        return attempt

            # Open an extreme position
            if markets[-1].prob() - markets[0].prob() > self.margin:
                return arb(
                    markets=[markets[0], markets[-1].inverse()],
                    target=1.0 - self.margin,
                    max_shares=INF,
                )

        res = find_opp()
        while res is not None and len(res) > 0:
            yield res
            res = find_opp()


@dataclass
class Ordering(DataClassJsonMixin):
    markets: list[Direction]
    margin: float = ORDERED_MARGIN

    def generate_opportunities(self) -> Iterator[list[RecommendedTrade]]:
        """
        We don't expect to ever find positions we can exit out of.
        Instead prioritize maximum gaps.
        """
        pass


@dataclass
class GeneralArbOpportunity(DataClassJsonMixin):
    maximum: float
    markets: list[Direction]
    max_shares: float = INF

    def generate_opportunities(self) -> Iterator[list[RecommendedTrade]]:
        markets = [VirtualMarket.from_direction(d) for d in self.markets]
        trades = arb(markets=markets, target=self.maximum, max_shares=self.max_shares)
        if len(trades) > 0:
            yield trades
