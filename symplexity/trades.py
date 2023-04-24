import logging
from dataclasses import dataclass
from typing import Optional

from symplexity.api import ApiError, Wrapper

import symplexity.market as market
from symplexity.basic_types import Outcome

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

    def cost(self) -> float:
        provisional = self.mana
        if self.outcome == "NO" and self.market.position > 0:
            # if we have YES shares we can sell them instead of buying NO
            adjustment = min(self.shares, self.market.position)
        elif self.outcome == "YES" and self.market.position < 0:
            adjustment = min(self.shares, -self.market.position)
        else:
            adjustment = 0
        return provisional - adjustment

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
    wrapper: Wrapper,
    trades: list[RecommendedTrade],
    dry_run: bool = True,
    max_cost: float = 0.0,
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
    total_cost = sum(trade.cost() for trade in trades)

    message = "Dry run" if dry_run else "Making"
    logger.info(f"{message} {len(trades)} trades for total M{total_cost}")
    if total_cost > max_cost:
        logger.info("Trades are too expensive")
        return False
    tokens = wrapper.lease_writes(len(trades))
    for token, trade in zip(tokens,trades):
        logger.info(f"{message} trade {trade}")
        if not dry_run:
            try:
                response = wrapper.make_bet(
                    mana=trade.mana,
                    market_id=trade.market.base.id,
                    outcome=trade.outcome,
                    token=token
                )
            except ApiError as e:
                error = TradeError(e.status, e.body, trade, trades)
                logger.error(error)
                raise error

    return True
