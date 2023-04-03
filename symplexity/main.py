from arb import ArbOpportunity, execute_arb
from config import init_logger, load_config
import argparse

def main(go: bool):
    dry_run = not go
    logger = init_logger()
    config = load_config()
    try:
        arb_opportunities = [ArbOpportunity.from_dict(d) for d in config['arb_opportunities']]
        for opportunity in arb_opportunities:
            execute_arb(opportunity, dry_run=dry_run)
    finally:
        for handler in logger.handlers:
            handler.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--go', action='store_true')
    args = parser.parse_args()
    main(args.go)