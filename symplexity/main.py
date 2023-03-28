from arb import execute_arb

arb_opportunities = [
    ("will-trump-be-indicted-by-march-31", "will-trump-be-indicted-by-march-31-4c8adb0a72fa")
]

def main():
    for (slug1, slug2) in arb_opportunities:
        print(f"Attempting arb of {slug1} and {slug2}")
        execute_arb(slug1, slug2)

if __name__ == "__main__":
    main()