import tempfile
import unittest
from pathlib import Path

from app.data.loaders import DataIngestor
from app.schemas.models import SourceType


class IngestionTests(unittest.TestCase):
    def test_valid_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ok.csv"
            p.write_text(
                "station_id,timestamp,temperature_c,pressure_hpa,relative_humidity_pct\nS1,2026-01-01T00:00:00Z,25,1008,70\n",
                encoding="utf-8",
            )
            result = DataIngestor().from_csv(p, dataset_id="d1", source_type=SourceType.SYNTHETIC)
            self.assertEqual(len(result.observations), 1)
            self.assertFalse(result.errors)
            self.assertEqual(result.provenance.record_count, 1)

    def test_malformed_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text(
                "station_id,timestamp,temperature_c,pressure_hpa,relative_humidity_pct\nS1,bad,warm,1008,70\n",
                encoding="utf-8",
            )
            result = DataIngestor().from_csv(p, dataset_id="d1")
            self.assertFalse(result.observations)
            self.assertEqual(result.errors[0].code, "malformed_record")

    def test_missing_columns(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "missing.csv"
            p.write_text("station_id,timestamp\nS1,2026-01-01T00:00:00Z\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                DataIngestor().from_csv(p, dataset_id="d1")

    def test_parquet_when_engine_available(self):
        try:
            import pyarrow  # noqa:F401
        except ImportError:
            self.skipTest("pyarrow unavailable in offline sandbox")
        import pandas as pd

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rows.parquet"
            pd.DataFrame(
                [
                    {
                        "station_id": "S1",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "temperature_c": 25,
                        "pressure_hpa": 1008,
                        "relative_humidity_pct": 70,
                    }
                ]
            ).to_parquet(p)
            self.assertEqual(len(DataIngestor().from_parquet(p, dataset_id="pq").observations), 1)
