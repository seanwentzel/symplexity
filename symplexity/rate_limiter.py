import time
import logging

logger = logging.getLogger("symplexity.rate_limiter")


class Token:
    def __init__(self) -> None:
        self.used = False

    def use(self) -> None:
        if not self.used:
            self.used = True
        else:
            raise RuntimeError("Tried to double-use rate limiting token")


class LeakyBucket:
    """
    Written by ChatGPT.
    """

    def __init__(self, capacity: float, rate_per_sec: float):
        self.capacity = capacity
        self.rate_per_sec = rate_per_sec
        self.last_update_time = time.monotonic()
        self.current_size = 0

    def lease(self, tokens: int) -> float | list[Token]:
        now = time.monotonic()
        elapsed_time = now - self.last_update_time
        self.current_size -= elapsed_time * self.rate_per_sec
        if self.current_size < 0:
            self.current_size = 0
        self.last_update_time = now
        if self.current_size + tokens <= self.capacity:
            self.current_size += tokens
            return [Token() for i in range(tokens)]
        else:
            return (self.current_size + tokens - self.capacity) / self.rate_per_sec
        
    def allow(self, tokens: int) -> bool:
        maybe_tokens = self.lease(tokens)
        if isinstance(maybe_tokens, float):
            return False
        else:
            return True
        
    def block_until_allowed(self, tokens: int) -> list[Token]:
        maybe_tokens = self.lease(tokens)
        if isinstance(maybe_tokens, float):
            sleep = maybe_tokens+0.05
            logger.info(f"Sleeping {sleep} seconds until tokens available")
            time.sleep(sleep)
        maybe_tokens = self.lease(tokens)
        assert not isinstance(maybe_tokens, float)
        return maybe_tokens


