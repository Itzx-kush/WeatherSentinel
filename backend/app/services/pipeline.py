"""Reproducible Part 1 pipeline: ingestion result -> validation -> past-only features."""

from pydantic import BaseModel

from app.data.quality import QualityValidator
from app.features.engine import FeatureEngine
from app.schemas.models import FeatureRecord, IngestionResult, QualityStatus


class PipelineResult(BaseModel):
    records: list[FeatureRecord]
    malformed_records: int
    valid_records: int
    suspect_records: int
    invalid_records: int
    dataset_id: str
    processing_version: str


class FoundationPipeline:
    def __init__(self, quality_config=None, feature_config=None):
        self.validator = QualityValidator(quality_config)
        self.features = FeatureEngine(feature_config)

    def run(self, ingestion: IngestionResult) -> PipelineResult:
        validated = self.validator.validate(ingestion.observations)
        records = self.features.transform(validated)
        counts = {s: 0 for s in QualityStatus}
        for r in records:
            counts[r.quality_status] += 1
        p = ingestion.provenance
        return PipelineResult(
            records=records,
            malformed_records=len(ingestion.errors),
            valid_records=counts[QualityStatus.VALID],
            suspect_records=counts[QualityStatus.SUSPECT],
            invalid_records=counts[QualityStatus.INVALID],
            dataset_id=p.dataset_id,
            processing_version=p.processing_version,
        )
