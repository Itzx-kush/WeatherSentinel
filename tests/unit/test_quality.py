import unittest

from app.data.quality import QualityConfig, QualityValidator
from app.schemas.models import AWSObservation


def row(ts, t=25, p=1008, h=70):
    return AWSObservation(
        station_id="S1", timestamp=ts, temperature_c=t, pressure_hpa=p, relative_humidity_pct=h
    )


class QualityTests(unittest.TestCase):
    def test_quality_failures_detected(self):
        rows = [
            row("2026-01-01T00:00:00Z"),
            row("2026-01-01T00:10:00Z"),
            row("2026-01-01T00:20:00Z"),
            row("2026-01-01T00:30:00Z"),
            row("2026-01-01T00:30:00Z"),
            row("2026-01-01T01:00:00Z", t=99, h=None),
        ]
        found = {
            f.code
            for r in QualityValidator(QualityConfig(freeze_consecutive=4)).validate(rows)
            for f in r.flags
        }
        self.assertTrue(
            {
                "frozen_value",
                "duplicate_timestamp",
                "communication_gap",
                "physical_range",
                "missing_value",
            }
            <= found
        )
