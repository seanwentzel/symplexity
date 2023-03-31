from arb import ArbOpportunity, execute_arb
from api import slug_to_id


def main():
    id1 = slug_to_id("will-trump-be-indicted-by-march-31")
    id2 = slug_to_id("will-trump-be-indicted-by-march-31-4c8adb0a72fa")
    arb_opportunities = [
        ArbOpportunity(0.995,[(id1, 'YES'), (id2, 'NO')]),
        ArbOpportunity(0.995,[(id1, 'NO'), (id2, 'YES')]),
    ]
    for opportunity in arb_opportunities:
        execute_arb(opportunity, dry_run=True)

if __name__ == "__main__":
    main()