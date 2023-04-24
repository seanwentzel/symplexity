import argparse
import itertools

import symplexity.api as api
from symplexity.config import init_logger, load_config
from symplexity.relationships import Equivalence, GeneralArbOpportunity
from symplexity.trades import execute_trades


def main(go: bool, max_cost: float, iterations_per_opp: int = 5):
    dry_run = not go
    if dry_run:
        # No point retrying the same opportunity over and over
        iterations_per_opp = 1
    logger = init_logger()
    config = load_config()

    try:
        # Try equiv
        equivalences = [Equivalence.from_dict(d) for d in config["equivalences"]]
        for relationship in equivalences:
            # There's something going wrong here
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
    finally:
        for handler in logger.handlers:
            handler.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", action="store_true")
    parser.add_argument("--max-cost", type=float, default=0.)
    args = parser.parse_args()
    main(args.go, args.max_cost)
