import itertools
from symplexity import api
from symplexity.relationships import Equivalence, GeneralArbOpportunity, Ordering
from symplexity.trades import execute_trades

def execute(dry_run: bool, max_cost: float, config: dict, iterations_per_opp: int = 1):
    #Equivalences
    equivalences = [Equivalence.from_dict(d) for d in config["equivalences"]]
    for relationship in equivalences:
        gen = itertools.islice(relationship.generate_opportunities(max_cost), iterations_per_opp)
        for recommended_trades in gen:
            execute_trades(api.wrapper, recommended_trades, dry_run=dry_run, max_cost=max_cost)

    # Orderings
    orderings = [Ordering.from_dict(d) for d in config["orderings"]]
    for relationship in orderings:
        gen = itertools.islice(relationship.generate_opportunities(max_cost), iterations_per_opp)
        for recommended_trades in gen:
            execute_trades(api.wrapper, recommended_trades, dry_run=dry_run, max_cost=max_cost)
    # General
    general_arb_opportunities = [
        GeneralArbOpportunity.from_dict(d) for d in config["arb_opportunities"]
    ]
    for opportunity in general_arb_opportunities:
        for recommended_trades in opportunity.generate_opportunities():
            execute_trades(api.wrapper, recommended_trades, dry_run=dry_run, max_cost=max_cost)