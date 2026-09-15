import unittest

from app.replay.engine import replay_observations
from app.schemas.models import AWSObservation


def row(ts, t):
    return AWSObservation(
        station_id="S1", timestamp=ts, temperature_c=t, pressure_hpa=1008, relative_humidity_pct=70
    )


class ReplayTests(unittest.IsolatedAsyncioTestCase):
    async def test_order_values_and_timing(self):
        rows = [row("2026-01-01T00:10:00Z", 22), row("2026-01-01T00:00:00Z", 20)]
        sleeps = []

        async def sleeper(delay):
            sleeps.append(delay)

        emitted = [
            x
            async for x in replay_observations(
                rows, speed=60, max_sleep_seconds=20, sleeper=sleeper
            )
        ]
        self.assertEqual([x.temperature_c for x in emitted], [20, 22])
        self.assertEqual(sleeps, [10])
        self.assertEqual(emitted[0].model_dump(), rows[1].model_dump())
