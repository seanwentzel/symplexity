# %%
import manifoldpy.api as api
import json
import requests
import math

# %%
def parse(response) -> dict:
    return json.loads(response.text)

# %%
with open('/Users/sean/tmp/manifold_key') as fin:
    api_key = fin.read().strip()

# %%
wrapper = api.APIWrapper(api_key)
# %%
me = parse(wrapper.me())
# %%
market1 = api.get_slug("will-trump-be-indicted-by-march-31")
market2 = api.get_slug("will-trump-be-indicted-by-march-31-4c8adb0a72fa")


# %%

def market_constant(p, y, n):
    return y**(p)*n**(1-p)

def prob(market):
    return raw_prob(market.p, market.pool["YES"], market.pool["NO"])
# %%
bets1 = api.get_bets(userId = me["id"],marketId=market1.id)

# %%
BASE_URI = "https://manifold.markets/api/v0"
def get_position(market):
    response = requests.get(f"{BASE_URI}/market/{market.id}/positions?userId={me['id']}")
    return response
# %%

def raw_prob(p, y, n):
    return p*n/((1-p)*y + p*n)

def invest_effect(inv, p, y, n):
    c = market_constant(p, y, n)
    y_2 = y + inv
    n_2 = n + inv
    y_t = (c  / (n_2)**(1-p))**(1./p)
    return y_2 - y_t, raw_prob(p, y_t, n_2)

EPS = 1e-4
INF = 1000.

def arb(m1, m2):
    prob1 = prob(m1)
    prob2 = prob(m2)
    if abs(prob1 - prob2) < 0.01:
        print(f"Not arbing because the markets are too close:")
        print(f"{prob1}, {m1.slug}")
        print(f"{prob2}, {m2.slug}")
        return []
    if prob1 > prob2:
        return arb(m2, m1)
    def target(k):
        _, p1, p2 = k_yes(k, m1, m2)
        return -(p2-p1-0.01)
    k_y = binary_search(target, 0., INF)
    k_n, p1, p2 =  k_yes(k_y,m1,m2)
    print("Market 1")
    print(m1.url)
    print(f"Buy M {k_y} YES to {p1}")
    print("Market 2")
    print(m2.url)
    print(f"Buy M {k_n} NO to {p2}")



def binary_search(fn, lo, hi):
    mid = (hi+lo)/2
    if hi - lo < EPS:
        return (hi+lo)/2
    if fn(mid) < 0:
        return binary_search(fn, mid, hi)
    else:
        return binary_search(fn, lo, mid)
    
def k_yes(k, m1, m2):
    s_y, m1_p = invest_effect(k, m1.p, m1.pool["YES"], m1.pool["NO"])
    def shares_no(inv_no):
        s_n, m2_p = invest_effect(inv_no, 1-m2.p, m2.pool["NO"], m2.pool["YES"])
        return s_n - s_y
    k_n = binary_search(shares_no,0.,INF)
    print(f"y: {k}, n: {k_n}")
    s_n, m2_p = invest_effect(k_n, 1-m2.p, m2.pool["NO"], m2.pool["YES"])
    m2_p = 1- m2_p
    print(m1_p, m2_p)
    return k_n, m1_p, m2_p
# %%
arb(market1, market2)
# %%
