# Symplexity
A bot which arbitrages markets on [Manifold](https://manifold.markets/). 
It can currently arbitrage two equivalent markets. Planning to add support for:
- balance management to make it much safer to cron
- ugh limit orders

Note that there are definitely edge cases where this can do the wrong thing, so I wouldn't just go running it all by itself just yet.

## How it works
The arbitrage script tries to buy positions of N shares in each of multiple positions,
so that the probabilities of each position still sum to less than some target.
In order to simplify the code, a NO position is modeled as a YES position in an
opposite market (one that resolves YES iff the original resolves NO).

This allows you to model many different opportunities, such as:
- two markets being equivalent
- two markets being mutually exclusive
- Exactly 1 of `N` markets resolving YES.