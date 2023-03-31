from dataclasses import dataclass
from dataclasses_json import dataclass_json

import market
from trades import RecommendedTrade, execute_trades, Outcome
from api import initialize

EPS = 1e-5
INF = 2000.0
ARB_LIMIT = 0.005


@dataclass_json
@dataclass
class ArbOpportunity:
    maximum: float
    markets: list[tuple[str, Outcome]]


def binary_search(fn, lo, hi):
    mid = (hi + lo) / 2
    if hi - lo < EPS:
        return mid
    if fn(mid) < 0:
        return binary_search(fn, mid, hi)
    else:
        return binary_search(fn, lo, mid)


def investment_for_shares(shares: float, market: market.VirtualMarket) -> float:
    """
    How much mana do you need to buy
    """
    def target(k):
        s, prob = market.invest_effect(k)
        return s - shares

    return binary_search(target, 0, INF)


def prob_for_shares(shares: float, market: market.VirtualMarket) -> float:
    k_y = investment_for_shares(shares, market)
    s, prob = market.invest_effect(k_y)
    assert shares * (1 - EPS) <= s <= shares * (1 + EPS), f"{shares}, {s}"
    return prob


def effective_prob(shares: float, markets: list[market.VirtualMarket]) -> float:
    return sum(prob_for_shares(shares, m) for m in markets)


def arb(opportunity: ArbOpportunity) -> list[RecommendedTrade]:
    target = opportunity.maximum
    markets = []
    for id, outcome in opportunity.markets:
        if outcome == "YES":
            markets.append(market.ApiMarket.from_id(id))
        elif outcome == "NO":
            markets.append(market.InverseMarket(market.ApiMarket.from_id(id)))
        else:
            raise RuntimeError("impossible code path")
    probs = [m.prob() for m in markets]
    if sum(probs) > target:
        print("Not arbing because there is no arbitrage gap.")
        return []

    def prob_centered(s):
        return effective_prob(s, markets) - target

    shares_to_buy = binary_search(prob_centered, 0, INF)
    result = []
    for m in markets:
        investment = investment_for_shares(shares_to_buy, m)
        result.append(RecommendedTrade.yes_for_virtual(investment, m))
    return result


def execute_arb(opportunity: ArbOpportunity, dry_run: bool = True):
    wrapper, me = initialize()
    if dry_run:
        wrapper = None
    trades = arb(opportunity)
    print("Ran arb, got the following trades:")
    for trade in trades:
        print(f"  - {trade}")
    result = execute_trades(wrapper, trades, dry_run=dry_run)
    if result:
        print("Succeeded arb")
    else:
        print("Validation failed")
