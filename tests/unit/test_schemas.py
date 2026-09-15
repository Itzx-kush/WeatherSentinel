import unittest
from datetime import datetime

from app.schemas.models import AWSObservation, StationMetadata
from pydantic import ValidationError


class SchemaTests(unittest.TestCase):
    def test_valid_normalizes_utc(self):
        row = AWSObservation(
            station_id="S1",
            timestamp="2026-01-01T05:30:00+05:30",
            temperature_c=25,
            pressure_hpa=1008,
            relative_humidity_pct=70,
        )
        self.assertEqual(row.timestamp.isoformat(), "2026-01-01T00:00:00+00:00")

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValidationError):
            AWSObservation(
                station_id="S1",
                timestamp=datetime(2026, 1, 1),
                temperature_c=25,
                pressure_hpa=1008,
                relative_humidity_pct=70,
            )

    def test_missing_field_rejected(self):
        with self.assertRaises(ValidationError):
            AWSObservation(
                station_id="S1",
                timestamp="2026-01-01T00:00:00Z",
                temperature_c=25,
                pressure_hpa=1008,
            )

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValidationError):
            AWSObservation(
                station_id="S1",
                timestamp="2026-01-01T00:00:00Z",
                temperature_c="warm",
                pressure_hpa=1008,
                relative_humidity_pct=70,
            )

    def test_station_coordinates_paired(self):
        with self.assertRaises(ValidationError):
            StationMetadata(station_id="S1", latitude=17.7)
