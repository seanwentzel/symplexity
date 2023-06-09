import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from symplexity.arb import arb
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

    def generate_opportunities(self, max_cost: float) -> Iterator[list[RecommendedTrade]]:
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
                        logger.info(f"Found exit for {attempt[0].shares} shares")
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
                        logger.info(f"Found transfer for {attempt[0].shares} shares")
                        return attempt

            # Open an extreme position
            if markets[-1].prob() - markets[0].prob() > self.margin:
                return arb(
                    markets=[markets[0], markets[-1].inverse()],
                    target=1.0 - self.margin,
                    max_shares=INF if max_cost is None else max_cost # max_cost is not perfect but it's close enough for now
                )

        res = find_opp()
        while res is not None and len(res) > 0:
            yield res
            res = find_opp()

    def __str__(self) -> str:
        res = "Equivalence:\n"
        for dir in self.directions:
            market = VirtualMarket.from_direction(dir)
            res += f"  - {market} {dir.id}\n"
        return res


@dataclass
class Ordering(DataClassJsonMixin):
    directions: list[Direction] #least to most probable
    margin: float = ORDERED_MARGIN

    def generate_opportunities(self, max_cost: float) -> Iterator[list[RecommendedTrade]]:
        """
        We don't expect to ever find positions we can exit out of.
        Instead prioritize maximum gaps.
        """
        def find_opp() -> Optional[list[RecommendedTrade]]:
            markets = [VirtualMarket.from_direction(d) for d in self.directions]
            positions = [market.position for market in markets]
            for m, p in zip(markets, positions):
                logger.debug("Looking for opportunities in:")
                logger.debug(f"Market: {m}, Position: {p}, Probability: {m.prob():.4f}")

            # Transfer 1-sided positions
            for i in range(len(markets)):
                for j in range(len(markets) - 1, i, -1):
                    if markets[i].prob() > markets[j].prob():
                        max_shares = max(positions[i], -positions[j])
                        attempt = arb(
                            markets=[markets[i].inverse(), markets[j]],
                            target=1.0,
                            max_shares=max_shares,
                        )
                        if len(attempt) > 0:
                            logger.info(f"Found transfer for {attempt[0].shares} shares")
                            return attempt
            # Enter positions
            for i in range(len(markets)):
                for j in range(len(markets) - 1, i, -1):
                    if markets[i].prob() > markets[j].prob():
                        attempt = arb(
                            markets=[markets[i].inverse(), markets[j]],
                            target=1.0-ORDERED_MARGIN,
                            max_shares=max_cost,
                        )
                        if len(attempt) > 0:
                            logger.info(f"Found new position for {attempt[0].shares} shares")
                            return attempt


        res = find_opp()
        while res is not None and len(res) > 0:
            yield res
            res = find_opp()



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

    def __str__(self) -> str:
        res = "General:\n"
        for dir in self.markets:
            market = VirtualMarket.from_direction(dir)
            res += f"  - {market} {dir.id}\n"
        return res
