# Symplexity
A bot which arbitrages markets on [Manifold](https://manifold.markets/). 
It can currently arbitrage two equivalent markets. Planning to add support for:
- one directional arbitrage where market X must be higher than market Y
- `n`-way arbitrage: make a single trade each on `n` related markets
- balance management to make it much safer

Note that there are definitely edge cases where this can do the wrong thing, so I wouldn't just go running it all by itself just yet.