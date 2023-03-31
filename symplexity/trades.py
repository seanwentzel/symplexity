import market
from dataclasses import dataclass
from typing import Literal
import manifoldpy.api as api

Outcome = Literal["YES", "NO"]


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
        return f"{self.market.base.url} // M {self.mana} {self.outcome} for {self.shares} shares to {self.expected_prob}"
    
    @staticmethod
    def yes_for_virtual(mana: float, target: market.VirtualMarket) -> "RecommendedTrade":
        shares, prob = target.invest_effect(mana)
        if isinstance(target, market.InverseMarket):
            return RecommendedTrade(target.base, mana, "NO", 1.-prob, shares)
        elif isinstance(target, market.ApiMarket):
            return RecommendedTrade(target, mana, "YES", prob, shares)


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


def execute_trades(wrapper: api.APIWrapper, trades: list[RecommendedTrade], dry_run: bool=True) -> bool:
    '''
    Check all the trades are still valid, then execute them. `print` out 
    details if the execution fails, since then we will end up with an uncovered
    position which may require intervention.
    '''
    validation = all(validate_market(t.market) for t in trades)
    if not validation:
        return False
    for trade in trades:
        if not dry_run:
            response = wrapper.make_bet(
                amount=trade.mana, contractId=trade.market.base.id, outcome=trade.outcome
            )
            if response.status_code != 200:
                print(
                    f"unable to complete trades: got status {response.status_code} for the following trade"
                )
                print(f"Response body: {response.text}")
                print(trade)
                print("all trades:")
                for t2 in trades:
                    print(t2)
                raise RuntimeError("Trade API error")
        else:
            print(f"Dry run trade {trade}")
    return True
