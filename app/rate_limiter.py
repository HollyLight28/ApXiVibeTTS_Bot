from __future__ import annotations

import asyncio
import os
import time


class RateLimiter:
    def __init__(self, rpm: int):
        if rpm <= 0:
            raise ValueError("rpm має бути > 0")
        self._rpm = rpm
        self._lock = asyncio.Lock()
        self._last = 0.0

    @property
    def rpm(self) -> int:
        return self._rpm

    def set_rpm(self, rpm: int) -> None:
        if rpm <= 0:
            raise ValueError("rpm має бути > 0")
        self._rpm = rpm

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            min_interval = 60.0 / float(self._rpm)
            delta = now - self._last
            if delta < min_interval:
                await asyncio.sleep(min_interval - delta)
            self._last = time.monotonic()


def env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if not val:
        return default
    try:
        return int(val)
    except Exception:
        return default

