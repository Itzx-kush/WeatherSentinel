import unittest
from datetime import UTC, datetime, timedelta

from app.detection.temporal_model import TemporalReconstructionDetector
from app.schemas.models import AWSObservation, DatasetProvenance, IngestionResult, SourceType
from app.services.pipeline import FoundationPipeline


def rows(n=36):
    return [
        AWSObservation(
            station_id="S1",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=10 * i),
            temperature_c=25 + 0.05 * i,
            pressure_hpa=1005 - 0.03 * i,
            relative_humidity_pct=70 - 0.04 * i,
        )
        for i in range(n)
    ]


class TemporalModelTests(unittest.TestCase):
    def features(self, data):
        ingestion = IngestionResult(
            observations=data,
            errors=[],
            provenance=DatasetProvenance(
                dataset_id="temporal-test",
                source_filename="generated",
                source_type=SourceType.SYNTHETIC,
                record_count=len(data),
            ),
        )
        return FoundationPipeline().run(ingestion).records

    def test_fit_and_inference(self):
        detector = TemporalReconstructionDetector(window_size=8, components=3, threshold=0.75)
        features = self.features(rows())
        detector.fit(features[:24], "temporal-test")
        detector.reset()
        outputs = [detector.detect(record)[0] for record in features]
        self.assertTrue(any(output.sufficient_history for output in outputs))
        self.assertTrue(any(output.features.get("model", {}).get("model_name") == "TemporalPCAAutoencoder" for output in outputs))

    def test_fitted_state_is_reproducible(self):
        features = self.features(rows())
        first = TemporalReconstructionDetector(window_size=8, components=3).fit(features[:24], "temporal-test")
        second = TemporalReconstructionDetector(window_size=8, components=3).fit(features[:24], "temporal-test")
        self.assertEqual(first.metadata.model_dump(), second.metadata.model_dump())
