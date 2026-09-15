import unittest
from pathlib import Path

from app.data.loaders import DataIngestor
from app.schemas.models import SourceType
from app.services.pipeline import FoundationPipeline


class PipelineTests(unittest.TestCase):
    def test_example_end_to_end(self):
        path = Path(__file__).parents[2] / "data/examples/aws_synthetic_normal.csv"
        loaded = DataIngestor().from_csv(
            path, dataset_id="demo-v1", source_type=SourceType.SYNTHETIC
        )
        result = FoundationPipeline().run(loaded)
        self.assertFalse(loaded.errors)
        self.assertEqual(len(result.records), 12)
        self.assertEqual(result.dataset_id, "demo-v1")
        self.assertIsNotNone(
            result.records[-1].temporal_features["temperature_c"]["rolling_median"]
        )

    def test_invalid_record_is_structured(self):
        loaded = DataIngestor().from_records(
            [
                {
                    "station_id": "S1",
                    "timestamp": "bad",
                    "temperature_c": "x",
                    "pressure_hpa": 1008,
                    "relative_humidity_pct": 70,
                }
            ],
            dataset_id="bad",
            source_filename="memory",
            source_type=SourceType.UNKNOWN,
        )
        result = FoundationPipeline().run(loaded)
        self.assertEqual(result.malformed_records, 1)
        self.assertEqual(result.records, [])
