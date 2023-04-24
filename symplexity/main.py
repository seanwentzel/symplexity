import argparse
import itertools
from symplexity import engine

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
        engine.execute(dry_run, max_cost, config, iterations_per_opp)
    finally:
        for handler in logger.handlers:
            handler.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", action="store_true")
    parser.add_argument("--max-cost", type=float, default=0.)
    args = parser.parse_args()
    main(args.go, args.max_cost)
