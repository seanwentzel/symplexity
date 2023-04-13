from dataclasses import dataclass
from dataclasses_json import dataclass_json

from basic_types import Direction, Outcome
from collections.abc import Iterator
import logging
from typing import Optional

import api
from arb import ArbOpportunity
from market import VirtualMarket

EQUIVALENT_MARGIN = 0.005
ORDERED_MARGIN = 0.02
INF = 2000.0

logger = logging.getLogger("symplexity.relationships")

@dataclass_json
@dataclass
class Equivalence:
    directions: list[Direction]
    margin: float = EQUIVALENT_MARGIN

    def generate_opportunities(self, me: dict) -> Iterator[ArbOpportunity]:
        """
        First, find positions we can exit out of at a profit.
        Second, find new dutch books.

        For now, we just use this method recursively!
        """

        def find_opp() -> Optional[ArbOpportunity]:
            markets = [VirtualMarket.from_direction(d) for d in self.directions]
            markets.sort(key=lambda m: m.prob())
            positions = [market.get_position(me) for market in markets]
            for m, p in zip(markets, positions):
                logger.debug("Looking for opportunities in:")
                logger.debug(f"Market: {m}, Position: {p}, Probability: {m.prob()}")
            for i, market in enumerate(markets):
                low_pos = positions[i]
                if low_pos > -1:
                    continue
                for j in range(i + 1, len(markets)):
                    hi_pos = positions[j]
                    if hi_pos < 1:
                        continue
                    logger.debug(f"High: {hi_pos}, low: {low_pos}")
                    logger.debug(f"High prob: {markets[j].prob()}, low prob: {market.prob()}")
                    max_shares = min(hi_pos, -low_pos)
                    logger.info(f"Found exit opportunity for M{max_shares}")
                    return ArbOpportunity(
                        maximum=1.0,  # we're exiting the position so we're gaining liquidity
                        markets=[market, markets[j].inverse()],
                        max_shares=max_shares,
                    )
            if markets[-1].prob() - markets[0].prob() > self.margin:
                return ArbOpportunity(
                    1.0 - self.margin,
                    markets=[markets[0], markets[-1].inverse()],
                    max_shares=INF,
                )

        res = find_opp()
        while res is not None:
            yield res
            res = find_opp()


@dataclass_json
@dataclass
class Ordering:
    markets: list[Direction]
    margin: float = ORDERED_MARGIN

    def generate_opportunities(self) -> Iterator[ArbOpportunity]:
        """
        We don't expect to ever find positions we can exit out of.
        Instead prioritize maximum gaps.
        """
        pass


@dataclass_json
@dataclass
class GeneralArbOpportunity:
    maximum: float
    markets: list[Direction]
    max_shares: float = INF

    def generate_opportunities(self) -> Iterator[ArbOpportunity]:
        markets = [VirtualMarket.from_direction(d) for d in self.markets]
        opp = ArbOpportunity(
            maximum=self.maximum, markets=markets, max_shares=self.max_shares
        )
        yield opp
