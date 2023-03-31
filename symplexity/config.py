import json

import os

def path() -> str:
    return os.path.join(os.getenv("HOME"), ".manifold_bot.json")

def load() -> dict:
    with open(path()) as fin:
        return json.load(fin)

def write(config: dict):
    # untested
    write_path = f"{path()}.write"
    with open(write_path, 'w') as fout:
        json.dump(config, fout)
    os.replace(src=write_path,dst=path())