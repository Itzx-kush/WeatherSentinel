from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

class EventBus:
    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    async def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            if not queue.full():
                queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)
