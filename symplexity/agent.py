import argparse
import time
from symplexity import engine

from symplexity.config import init_logger, load_config

def main(go: bool, wait_between_runs_s: float = 5):
    dry_run = not go
    logger = init_logger()
    config = load_config()
    while True:
        try:
            engine.execute(dry_run, max_cost=0, config=config)
        finally:
            for handler in logger.handlers:
                handler.flush()
        logger.info(f"Waiting {wait_between_runs_s}s before next cycle")
        time.sleep(wait_between_runs_s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", action="store_true")
    args = parser.parse_args()
    main(args.go)