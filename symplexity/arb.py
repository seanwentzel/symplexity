import market
from trades import RecommendedTrade, execute_trades
from api import initialize

EPS = 1e-5
INF = 2000.0
ARB_LIMIT = 0.005


def arb(m1: market.ApiMarket, m2: market.ApiMarket) -> list[RecommendedTrade]:
    prob1 = m1.prob()
    prob2 = m2.prob()
    if abs(prob1 - prob2) < ARB_LIMIT:
        print(f"Not arbing because the markets are too close:")
        print(f"{prob1}, {m1.base.slug}")
        print(f"{prob2}, {m2.base.slug}")
        return []
    if prob1 > prob2:
        return arb(m2, m1)

    def target(k):
        _, p1, p2 = k_yes(k, m1, m2)
        return -(p2 - p1 - ARB_LIMIT)

    k_y = binary_search(target, 0.0, INF)
    k_n, p1, p2 = k_yes(k_y, m1, m2)
    arb1 = RecommendedTrade(m1, k_y, "YES", p1)
    arb2 = RecommendedTrade(m2, k_n, "NO", p2)
    return [arb1, arb2]


def binary_search(fn, lo, hi):
    mid = (hi + lo) / 2
    if hi - lo < EPS:
        return mid
    if fn(mid) < 0:
        return binary_search(fn, mid, hi)
    else:
        return binary_search(fn, lo, mid)


def k_yes(k: float, m1: market.ApiMarket, m2: market.ApiMarket):
    s_y, m1_p = m1.invest_effect(k)

    m2_inv = market.InverseMarket(m2)

    def shares_no(inv_no):
        s_n, m2_p = m2_inv.invest_effect(inv_no)
        return s_n - s_y

    k_n = binary_search(shares_no, 0.0, INF)
    s_n, m2_p = m2_inv.invest_effect(k_n)
    m2_p = 1 - m2_p
    return k_n, m1_p, m2_p


def execute_arb(slug1: str, slug2: str):
    wrapper, me = initialize()
    market1 = market.ApiMarket.from_slug(slug1)
    market2 = market.ApiMarket.from_slug(slug2)
    trades = arb(market1, market2)
    print("Ran arb, got the following trades:")
    for trade in trades:
        print(f"  - {trade}")
    result = execute_trades(wrapper, trades)
    if result:
        print("Succeeded arb")
    else:
        print("Something went wrong!")
