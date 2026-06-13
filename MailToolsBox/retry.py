"""Retry/backoff and rate-limiting helpers for high-volume sending.

These primitives are transport-agnostic so the same policy objects can be
reused by the sync and async send paths.
"""

from __future__ import annotations

import asyncio
import random
import threading
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Tuple, Type, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Exponential backoff with optional jitter.

    ``delay = min(max_delay, base_delay * factor ** attempt)`` and, when
    ``jitter`` is set, a uniform random fraction of that delay is added. A
    policy with ``max_attempts=1`` disables retrying.
    """

    max_attempts: int = 3
    base_delay: float = 0.5
    factor: float = 2.0
    max_delay: float = 30.0
    jitter: float = 0.1
    retry_on: Tuple[Type[BaseException], ...] = (Exception,)

    def delay_for(self, attempt: int) -> float:
        """Backoff delay (seconds) before the given zero-based retry attempt."""
        raw = self.base_delay * (self.factor**attempt)
        capped = min(self.max_delay, raw)
        if self.jitter:
            capped += random.uniform(0, capped * self.jitter)
        return capped

    def run(self, func: Callable[[], T]) -> T:
        """Call ``func`` synchronously, retrying per this policy."""
        attempt = 0
        while True:
            try:
                return func()
            except self.retry_on as exc:
                attempt += 1
                if attempt >= self.max_attempts:
                    raise
                time.sleep(self.delay_for(attempt - 1))
                _ = exc  # retained for readability/debugging

    async def run_async(self, func: Callable[[], Awaitable[T]]) -> T:
        """Await ``func`` , retrying per this policy."""
        attempt = 0
        while True:
            try:
                return await func()
            except self.retry_on:
                attempt += 1
                if attempt >= self.max_attempts:
                    raise
                await asyncio.sleep(self.delay_for(attempt - 1))


class RateLimiter:
    """Token-bucket limiter capping throughput to ``rate`` operations/second.

    Thread-safe for the sync path; an async-aware ``acquire_async`` is provided
    for the asyncio path. ``rate <= 0`` disables limiting.
    """

    def __init__(self, rate: float, burst: float | None = None) -> None:
        self.rate = float(rate)
        self.capacity = float(burst) if burst is not None else max(self.rate, 1.0)
        self._tokens = self.capacity
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def _take(self) -> float:
        """Reserve a token; return seconds to wait before it is available."""
        now = time.monotonic()
        elapsed = now - self._updated
        self._updated = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return 0.0
        return (1.0 - self._tokens) / self.rate

    def acquire(self) -> None:
        if self.rate <= 0:
            return
        with self._lock:
            wait = self._take()
        if wait > 0:
            time.sleep(wait)

    async def acquire_async(self) -> None:
        if self.rate <= 0:
            return
        with self._lock:
            wait = self._take()
        if wait > 0:
            await asyncio.sleep(wait)
