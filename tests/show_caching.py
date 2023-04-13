import requests

from symplexity.api import create_test_market, initialize


wrapper, me = initialize()
id1 = create_test_market(wrapper, "market 1") 
print(requests.get(f"https://manifold.markets/api/v0/market/{id1}").text)
wrapper.make_bet(
                amount=5,
                contractId=id1,
                outcome="YES",
            )
print(requests.get(f"https://manifold.markets/api/v0/market/{id1}?cachebuster=123").text)
