from typing import Iterator

import symplexity.api as api
import symplexity.config as config
from symplexity.basic_types import Direction
from symplexity.relationships import (Equivalence, GeneralArbOpportunity,
                                      Ordering)


def capture_directions() -> Iterator[Direction]:
    print("Enter positions as `YES/NO url` [enter to finish]")
    while True:
        pos = input().strip()
        if pos == "":
            return
        else:
            segments = pos.split()
            if len(segments) == 1:
                outcome = "YES"
                url = segments[0]
            elif len(segments) == 2:
                outcome, url = segments
            else:
                raise RuntimeError("bad input")
            if outcome not in ["YES", "NO"]:
                raise RuntimeError("bad outcome")
            slug = url.split("/")[-1]
            id = api.slug_to_id(slug)
            yield Direction(id, outcome)


def capture_general_opp() -> GeneralArbOpportunity:
    print("What is the maximum total probability? [Enter 100% as 1.0]")
    maximum = float(input())
    directions = list(capture_directions())
    return GeneralArbOpportunity(maximum, directions)

def capture_equivalence() -> Equivalence:
    directions = list(capture_directions())
    return Equivalence(directions)

def capture_ordering() -> Ordering:
    directions = list(capture_directions())
    return Ordering(directions)

def main():
    conf = config.load_config()
    print("""Type:
    1. Equivalence
    2. Sequence
    3. General
    """)
    typ = int(input().strip())
    assert typ in [1,2,3]
    if typ == 1:
        conf["equivalences"].append(capture_equivalence().to_dict())
    elif typ == 2:
        conf["orderings"].append(capture_ordering().to_dict())
    elif typ == 3:
        conf["arb_opportunities"].append(capture_general_opp().to_dict())
    
    config.write_config(conf)


if __name__ == "__main__":
    main()
