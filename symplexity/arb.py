import logging
from dataclasses import dataclass

import symplexity.market as market
from symplexity.api import initialize
from symplexity.trades import RecommendedTrade, execute_trades

EPS = 1e-5

logger = logging.getLogger("symplexity.arb")


@dataclass
class ArbOpportunity:
    maximum: float
    markets: list[market.VirtualMarket]
    max_shares: float


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
    How much mana do you need to buy `shares` shares
    """

    def target(k):
        s, prob = market.invest_effect(k)
        return s - shares

    return binary_search(target, 0, shares)  # assuming each share costs < M1


def prob_for_shares(shares: float, market: market.VirtualMarket) -> float:
    k_y = investment_for_shares(shares, market)
    s, prob = market.invest_effect(k_y)
    # assert shares * (1 - 10*EPS) <= s <= shares * (1 + 10*EPS), f"{shares}, {s}"
    return prob


def effective_prob(shares: float, markets: list[market.VirtualMarket]) -> float:
    return sum(prob_for_shares(shares, m) for m in markets)


def arb(markets: list[market.VirtualMarket], target: float, max_shares: float) -> list[RecommendedTrade]:
    probs = [m.prob() for m in markets]
    if sum(probs) > target:
        logger.debug("Not arbing because there is no arbitrage gap.")
        return []

    def prob_centered(s):
        return effective_prob(s, markets) - target

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
    logger.info(
        f"Cost: M{sum(trade.mana for trade in result)}, Shares: {shares_to_buy}, Min value: M{target*shares_to_buy}"
    )
    return result


def execute_arb(opportunity: ArbOpportunity, dry_run: bool = True) -> int:
    wrapper, me = initialize()
    if dry_run:
        wrapper = None
    trades = arb(opportunity)
    logger.info(f"Ran arb, got {len(trades)} trades.")
    result = execute_trades(wrapper, trades, dry_run=dry_run)
    if result:
        logger.info("Succeeded arb")
        return len(trades)
    else:
        logger.warn("Validation failed")
        return -1
