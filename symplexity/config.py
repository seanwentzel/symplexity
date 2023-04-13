import json
import logging
import logging.handlers as handlers

import os
import sys

ROOT_DIR = os.path.join(os.getenv("HOME"), ".symplexity")
LOG_PATH = os.path.join(ROOT_DIR, "logs/symplexity.log")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH) as fin:
        return json.load(fin)


def write_config(config: dict):
    write_path = f"{CONFIG_PATH}.write"
    with open(write_path, "w") as fout:
        json.dump(config, fout, indent=2)
    os.replace(src=write_path, dst=CONFIG_PATH)


def init_logger() -> logging.Logger:
    logger = logging.getLogger("symplexity")
    logger.setLevel(logging.INFO)
    file_handler = handlers.TimedRotatingFileHandler(LOG_PATH, when="D")
    out_handler = logging.StreamHandler(sys.stdout)
    formatter=logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    out_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(out_handler)
    return logger
