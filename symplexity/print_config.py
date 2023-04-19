from symplexity import config
from symplexity.relationships import Equivalence, GeneralArbOpportunity

conf = config.load_config()
for equiv in conf["equivalences"]:
    print(Equivalence.from_dict(equiv))
for opp in conf["arb_opportunities"]:
    print(GeneralArbOpportunity.from_dict(opp))
