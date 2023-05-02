# Symplexity

A bot which arbitrages markets on [Manifold](https://manifold.markets/).
It can currently arbitrage two equivalent markets. Planning to add support for:

- balance management to make it much safer to cron
- ugh limit orders

Note that there are definitely edge cases where this can do the wrong thing, so I wouldn't just go running it all by itself just yet.

## Relationships between markets

A `Direction` is a particular outcome on a particular market.
The bot works by exploiting some known relationship between Directions.
Currently supported relationships:

- `N` directions should sum to at least `p` (`GeneralArbOpportunity`)
- A set of directions are equivalent to each other (and will all resolve the same way).
- A sequence of directions should be ordered from least to most probable.
- (coming later) "Bayesian quadrangles": four markets for `A`, `B`, `B | A` and `B | !A`

## How it works

The arbitrage script tries to buy positions of N shares in each of multiple positions,
so that the probabilities of each position still sum to less than some target.
In order to simplify the code, a NO position is modeled as a YES position in an
opposite market (one that resolves YES iff the original resolves NO).

This allows you to model many different opportunities, such as:

- two markets being equivalent
- two markets being mutually exclusive
- Exactly 1 of `N` markets resolving YES.

## API usage

The Manifold API caches requests for 15 seconds. Volume is low, but this is very dangerous
if you want to arbitrage the same market multiple times. To get around this we insert a cachebusting
param into each request. This means we can't directly use the `manifoldpy` API.

To avoid [overusing](https://docs.manifold.markets/api#usage-guidelines) the API, we rate limit our access. For reads
especially, we should limit much lower than the requested rate.