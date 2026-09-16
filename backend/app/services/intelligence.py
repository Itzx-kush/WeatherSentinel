from pydantic import BaseModel
from app.detection.contracts import AnomalyResult
from app.detection.detectors import IsolationForestDetector, MultivariateDetector, RuleDetector, StatisticalDetector, TemporalDetector
from app.detection.fusion import FusionEngine
from app.diagnosis.engine import Diagnosis, DiagnosisEngine
from app.health.tracker import HealthSnapshot, HealthTracker
from app.schemas.models import FeatureRecord, IngestionResult
from app.services.pipeline import FoundationPipeline

class IntelligenceRecord(BaseModel):
    feature_record: FeatureRecord
    anomaly: AnomalyResult
    diagnosis: Diagnosis
    health: HealthSnapshot

class IntelligenceResult(BaseModel):
    dataset_id: str
    records: list[IntelligenceRecord]

class IntelligenceService:
    def __init__(self, ml: IsolationForestDetector | None = None):
        self.ml = ml or IsolationForestDetector()
        self.detectors = [RuleDetector(), StatisticalDetector(), TemporalDetector(), MultivariateDetector(), self.ml]
        self.fusion = FusionEngine()
        self.diagnoser = DiagnosisEngine()
        self.health = HealthTracker()

    def analyze(self, features: list[FeatureRecord], *, fit_ml: bool = True, dataset_id: str = "runtime") -> list[IntelligenceRecord]:
        if fit_ml:
            trainable = [r for r in features if all(getattr(r.observation, s) is not None for s in ("temperature_c", "pressure_hpa", "relative_humidity_pct"))]
            if len(trainable) >= 8:
                self.ml.fit(trainable, dataset_id)
        out = []
        for r in features:
            evidence = []
            for detector in self.detectors:
                evidence.extend(detector.detect(r))
            anomaly = self.fusion.fuse(evidence)
            out.append(IntelligenceRecord(feature_record=r, anomaly=anomaly, diagnosis=self.diagnoser.diagnose(anomaly), health=self.health.update(anomaly)))
        return out

    def run(self, ingestion: IngestionResult) -> IntelligenceResult:
        features = FoundationPipeline().run(ingestion).records
        return IntelligenceResult(dataset_id=ingestion.provenance.dataset_id, records=self.analyze(features, dataset_id=ingestion.provenance.dataset_id))
