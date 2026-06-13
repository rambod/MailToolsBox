import asyncio
import time

import pytest

from MailToolsBox.retry import RateLimiter, RetryPolicy


def test_retry_succeeds_after_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("transient")
        return "ok"

    policy = RetryPolicy(max_attempts=5, base_delay=0, jitter=0)
    assert policy.run(flaky) == "ok"
    assert calls["n"] == 3


def test_retry_gives_up_after_max_attempts():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise ValueError("nope")

    policy = RetryPolicy(max_attempts=3, base_delay=0, jitter=0)
    with pytest.raises(ValueError):
        policy.run(always_fails)
    assert calls["n"] == 3


def test_retry_only_catches_listed_exceptions():
    def boom():
        raise KeyError("unlisted")

    policy = RetryPolicy(max_attempts=3, base_delay=0, retry_on=(ValueError,))
    with pytest.raises(KeyError):
        policy.run(boom)


def test_retry_backoff_is_exponential():
    policy = RetryPolicy(base_delay=1.0, factor=2.0, jitter=0)
    assert policy.delay_for(0) == 1.0
    assert policy.delay_for(1) == 2.0
    assert policy.delay_for(2) == 4.0


def test_retry_respects_max_delay():
    policy = RetryPolicy(base_delay=10.0, factor=10.0, max_delay=15.0, jitter=0)
    assert policy.delay_for(3) == 15.0


def test_async_retry_succeeds_after_failures():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("transient")
        return "ok"

    policy = RetryPolicy(max_attempts=3, base_delay=0, jitter=0)
    assert asyncio.run(policy.run_async(flaky)) == "ok"
    assert calls["n"] == 2


def test_rate_limiter_throttles_throughput():
    limiter = RateLimiter(rate=20, burst=1)  # ~50ms between ops after the first
    start = time.monotonic()
    for _ in range(4):
        limiter.acquire()
    elapsed = time.monotonic() - start
    # 3 waits of ~50ms each; allow generous lower bound to avoid flakiness
    assert elapsed >= 0.1


def test_rate_limiter_disabled_when_rate_zero():
    limiter = RateLimiter(rate=0)
    start = time.monotonic()
    for _ in range(100):
        limiter.acquire()
    assert time.monotonic() - start < 0.05
