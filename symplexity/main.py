from arb import execute_arb
from config import init_logger, load_config
from relationships import GeneralArbOpportunity
import argparse

from market import ApiMarket
from relationships import Equivalence
from basic_types import Direction
from api import initialize


def main(go: bool):
    dry_run = not go
    logger = init_logger()
    config = load_config()
    wrapper, me = initialize()
    try:
        # Try equiv
        slugs = [
            "will-recep-tayyip-erdogan-be-reelec",
            "will-erdogan-win-the-2023-turkish-p-8691b1f6a772",
            "will-erdogan-win-the-2023-turkish-p",
        ]
        ids = [ApiMarket.from_slug(s).base.id for s in slugs]
        equivalence = Equivalence([Direction(id, "YES") for id in ids])
        gen = equivalence.generate_opportunities(me)
        opp = next(gen)
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
