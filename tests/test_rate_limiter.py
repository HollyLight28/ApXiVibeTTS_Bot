import asyncio
import time

import pytest

from app.rate_limiter import RateLimiter


def test_rate_limiter_enforces_interval() -> None:
    rl = RateLimiter(60)
    t0 = time.monotonic()
    asyncio.run(rl.acquire())
    asyncio.run(rl.acquire())
    t1 = time.monotonic()
    assert t1 - t0 >= 1.0


def test_set_rpm_validation() -> None:
    rl = RateLimiter(1)
    with pytest.raises(ValueError):
        rl.set_rpm(0)
