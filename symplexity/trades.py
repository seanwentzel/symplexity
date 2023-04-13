import market
from dataclasses import dataclass
from typing import Optional
from basic_types import Outcome
import manifoldpy.api as api

import logging

logger = logging.getLogger("symplexity.trades")


@dataclass
class RecommendedTrade:
    """
    Recommend buying `mana` of `outcome` on `market`,
    moving the market to `expected_prob`
    """

    market: market.ApiMarket
    mana: float
    outcome: Outcome
    expected_prob: float
    shares: float

    def __repr__(self):
        return f"{self.market.base.url} // M {self.mana:.2f} {self.outcome} for {self.shares:.2f} shares to {self.expected_prob:.4f}"

    @staticmethod
    def yes_for_virtual(
        mana: float, target: market.VirtualMarket
    ) -> "RecommendedTrade":
        shares, prob = target.invest_effect(mana)
        if isinstance(target, market.InverseMarket):
            return RecommendedTrade(target.base, mana, "NO", 1.0 - prob, shares)
        elif isinstance(target, market.ApiMarket):
            return RecommendedTrade(target, mana, "YES", prob, shares)


class TradeError(RuntimeError):
    status_code: Optional[int]
    body: Optional[str]
    trade: RecommendedTrade

    all_trades: list[RecommendedTrade]

    def __init__(
        self,
        status_code: Optional[int],
        body: Optional[str],
        trade: RecommendedTrade,
        all_trades: list[RecommendedTrade],
    ) -> None:
        super().__init__(
            "Code:",
            status_code,
            "Body:",
            body,
            "bad trade: ",
            trade,
            "all: ",
            all_trades,
        )
        self.status_code = status_code
        self.body = body
        self.trade = trade
        self.all_trades = all_trades


def validate_market(market: market.ApiMarket) -> bool:
    """
    Returns whether the `market` is the same as the last time
      we read it, to the best of our knowledge.
    """
    updated_market = market.latest()
    if market.prob() != updated_market.prob():
        return False
    if updated_market.base.isResolved:
        return False
    return market.total_liquidity() == updated_market.total_liquidity()


def execute_trades(
    wrapper: api.APIWrapper, trades: list[RecommendedTrade], dry_run: bool = True
) -> bool:
    """
    Check all the trades are still valid, then execute them. `print` out
    details if the execution fails, since then we will end up with an uncovered
    position which may require intervention.
    """
    validation = all(validate_market(t.market) for t in trades)
    if not validation:
        logger.warn("Validation failed on trades")
        for trade in trades:
            logger.warn(f"  - {trade}")
        return False
    message = "Dry run" if dry_run else "Making"
    for trade in trades:
        logger.info(f"{message} trade {trade}")
        if not dry_run:
            response = wrapper.make_bet(
                amount=trade.mana,
                contractId=trade.market.base.id,
                outcome=trade.outcome,
            )
            if response.status_code != 200:
                error = TradeError(response.status_code, response.text, trade, trades)
                logger.error(error)
                raise error

    return True
