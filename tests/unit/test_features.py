import unittest

from app.data.quality import QualityValidator
from app.features.engine import FeatureEngine
from app.schemas.models import AWSObservation


def make(ts, t):
    return AWSObservation(
        station_id="S1", timestamp=ts, temperature_c=t, pressure_hpa=1008, relative_humidity_pct=70
    )


class FeatureTests(unittest.TestCase):
    def test_past_only_and_deterministic(self):
        rows = [
            make("2026-01-01T00:00:00Z", 20),
            make("2026-01-01T00:10:00Z", 22),
            make("2026-01-01T00:20:00Z", 24),
        ]
        valid = QualityValidator().validate(rows)
        a = FeatureEngine().transform(valid)
        b = FeatureEngine().transform(valid)
        self.assertIsNone(a[0].temporal_features["temperature_c"]["rolling_mean"])
        self.assertEqual(a[1].temporal_features["temperature_c"]["rolling_mean"], 20)
        self.assertEqual(a[2].temporal_features["temperature_c"]["rolling_mean"], 21)
        self.assertEqual(a, b)
        self.assertIsNotNone(a[0].multivariate_features["dew_point_c"])
