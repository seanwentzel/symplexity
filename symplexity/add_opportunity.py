import api
import config
from relationships import GeneralArbOpportunity
from basic_types import Direction


def main():
    print("What is the maximum total probability? [Enter 100% as 1.0]")
    maximum = float(input())
    print("Enter positions as `YES/NO url` [enter to finish]")
    done = False
    directions = []
    while not done:
        pos = input().strip()
        if pos == "":
            done = True
        else:
            outcome, url = pos.split()
            if outcome not in ["YES", "NO"]:
                raise RuntimeError("bad outocme")
            slug = url.split("/")[-1]
            id = api.slug_to_id(slug)
            directions.append(Direction(id, outcome))
    arb = GeneralArbOpportunity(maximum, directions)

    conf = config.load_config()
    conf["arb_opportunities"].append(arb.to_dict())
    config.write_config(conf)


if __name__ == "__main__":
    main()
