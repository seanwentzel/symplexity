import requests

from symplexity.api import Wrapper, create_test_market

my_wrapper = Wrapper.from_config()
id1 = create_test_market(my_wrapper, "market 1")
print(requests.get(f"https://manifold.markets/api/v0/market/{id1}").text)
print(my_wrapper.market(id1).pool)

(token,) = my_wrapper.lease_writes(1)
my_wrapper.make_bet(mana=5, market_id=id1, outcome="YES", token=token)

print(requests.get(f"https://manifold.markets/api/v0/market/{id1}").text)
print(my_wrapper.market(id1).pool)
