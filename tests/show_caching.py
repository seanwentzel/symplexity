import requests

from symplexity.api import create_test_market, initialize, Wrapper


wrapper, me = initialize()
my_wrapper = Wrapper.from_config()
id1 = create_test_market(wrapper, "market 1") 
print(requests.get(f"https://manifold.markets/api/v0/market/{id1}").text)
print(my_wrapper.market(id1).pool)
wrapper.make_bet(
                amount=5,
                contractId=id1,
                outcome="YES",
            )
print(requests.get(f"https://manifold.markets/api/v0/market/{id1}").text)
print(my_wrapper.market(id1).pool)
