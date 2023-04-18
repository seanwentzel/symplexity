import argparse
import itertools

from symplexity.api import initialize
from symplexity.config import init_logger, load_config
from symplexity.relationships import Equivalence, GeneralArbOpportunity
from symplexity.trades import execute_trades



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
            gen = itertools.islice(relationship.generate_opportunities(), 1)
            for recommended_trades in gen:
                execute_trades(wrapper, recommended_trades, dry_run=dry_run)

        # General
        general_arb_opportunities = [
            GeneralArbOpportunity.from_dict(d) for d in config["arb_opportunities"]
        ]
        for opportunity in general_arb_opportunities:
            for recommended_trades in opportunity.generate_opportunities():
                execute_trades(wrapper, recommended_trades, dry_run=dry_run)
    finally:
        for handler in logger.handlers:
            handler.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", action="store_true")
    args = parser.parse_args()
    main(args.go)
