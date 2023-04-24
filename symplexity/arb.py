import logging
from dataclasses import dataclass
from typing import Callable

import symplexity.market as market
from symplexity.trades import RecommendedTrade

EPS = 1e-5

logger = logging.getLogger("symplexity.arb")


@dataclass
class ArbOpportunity:
    maximum: float
    markets: list[market.VirtualMarket]
    max_shares: float


def binary_search(fn: Callable[[float], bool], lo, hi):
    mid = (hi + lo) / 2
    if hi - lo < EPS:
        return mid
    if not fn(mid):
        return binary_search(fn, mid, hi)
    else:
        return binary_search(fn, lo, mid)


def investment_for_shares(shares: float, market: market.VirtualMarket) -> float:
    """
    How much mana do you need to buy `shares` shares
    """

    def target(k: float) -> bool:
        s, prob = market.invest_effect(k)
        return s > shares

    return binary_search(target, 0, shares)  # assuming each share costs < M1


def prob_for_shares(shares: float, market: market.VirtualMarket) -> float:
    k_y = investment_for_shares(shares, market)
    s, prob = market.invest_effect(k_y)
    # assert shares * (1 - 10*EPS) <= s <= shares * (1 + 10*EPS), f"{shares}, {s}"
    return prob


def effective_prob(shares: float, markets: list[market.VirtualMarket]) -> float:
    return sum(prob_for_shares(shares, m) for m in markets)


def arb(
    markets: list[market.VirtualMarket], target: float, max_shares: float
) -> list[RecommendedTrade]:
    probs = [m.prob() for m in markets]
    if sum(probs) > target:
        logger.debug("Not arbing because there is no arbitrage gap.")
        return []

    def prob_centered(s: float) -> bool:
        return effective_prob(s, markets) >= target

    shares_to_buy = binary_search(prob_centered, 0, max_shares)
    if shares_to_buy < 0.1:
        logger.debug("Not arbing because opportunity is tiny")
        return []
    result = []
    for m in markets:
        investment = investment_for_shares(shares_to_buy, m)
        if investment <= 1.0:
            logger.debug("Not arbing because investment too small")
            return []
        result.append(RecommendedTrade.yes_for_virtual(investment, m))
    assert effective_prob(shares_to_buy, markets) < target + EPS
    return result
