import argparse
import itertools

from symplexity.api import initialize
from symplexity.arb import execute_arb
from symplexity.config import init_logger, load_config
from symplexity.relationships import Equivalence, GeneralArbOpportunity


def main(go: bool):
    dry_run = not go
    logger = init_logger()
    config = load_config()
    wrapper, me = initialize()
    try:
        # Try equiv
        equivalences = [Equivalence.from_dict(d) for d in config["equivalences"]]
        for relationship in equivalences:
            # There's something going wrong here
            gen = itertools.islice(relationship.generate_opportunities(me), 1)
            for opp in gen:
                execute_arb(opp, dry_run=dry_run)

        # General
        general_arb_opportunities = [
            GeneralArbOpportunity.from_dict(d) for d in config["arb_opportunities"]
        ]
        for opportunity in general_arb_opportunities:
            for arb_opportunity in opportunity.generate_opportunities():
                execute_arb(arb_opportunity, dry_run=dry_run)
    finally:
        for handler in logger.handlers:
            handler.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", action="store_true")
    args = parser.parse_args()
    main(args.go)
