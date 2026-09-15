"""Timestamp-faithful replay; speed=0 is deterministic no-wait test mode."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

from app.schemas.models import AWSObservation

Sleeper = Callable[[float], Awaitable[None]]


async def replay_observations(
    observations: list[AWSObservation],
    *,
    speed: float = 60,
    max_sleep_seconds: float = 5,
    sleeper: Sleeper = asyncio.sleep,
) -> AsyncIterator[AWSObservation]:
    if speed < 0:
        raise ValueError("speed must be non-negative")
    prior = None
    for row in sorted(observations, key=lambda x: x.timestamp):
        if prior is not None and speed > 0:
            delay = max(0, (row.timestamp - prior.timestamp).total_seconds() / speed)
            await sleeper(min(delay, max_sleep_seconds))
        yield row
        prior = row
