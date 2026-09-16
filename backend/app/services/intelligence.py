from pydantic import BaseModel
from app.detection.contracts import AnomalyResult
from app.detection.detectors import IsolationForestDetector, MultivariateDetector, RuleDetector, StatisticalDetector, TemporalDetector
from app.detection.fusion import FusionEngine
from app.detection.temporal_model import TemporalReconstructionDetector
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
    def __init__(self, ml: IsolationForestDetector | None = None, temporal: TemporalReconstructionDetector | None = None):
        self.ml = ml or IsolationForestDetector()
        self.temporal_model = temporal or TemporalReconstructionDetector()
        self.detectors = [
            RuleDetector(),
            StatisticalDetector(),
            TemporalDetector(),
            MultivariateDetector(),
            self.ml,
            self.temporal_model,
        ]
        self.fusion = FusionEngine()
        self.diagnoser = DiagnosisEngine()
        self.health = HealthTracker()

    @staticmethod
    def _complete(features: list[FeatureRecord]) -> list[FeatureRecord]:
        sensors = ("temperature_c", "pressure_hpa", "relative_humidity_pct")
        return [r for r in features if all(getattr(r.observation, s) is not None for s in sensors)]

    def analyze(self, features: list[FeatureRecord], *, fit_ml: bool = True, dataset_id: str = "runtime") -> list[IntelligenceRecord]:
        trainable = self._complete(features)
        if fit_ml:
            if not self.ml.trees and len(trainable) >= 8:
                self.ml.fit(trainable, dataset_id)
            if not self.temporal_model.fitted and len(trainable) >= 20:
                split = max(self.temporal_model.window_size + 7, int(len(trainable) * 0.5))
                self.temporal_model.fit(trainable[:split], dataset_id)
        self.temporal_model.reset()
        self.health = HealthTracker()
        out = []
        for r in features:
            evidence = []
            for detector in self.detectors:
                evidence.extend(detector.detect(r))
            anomaly = self.fusion.fuse(evidence)
            out.append(IntelligenceRecord(feature_record=r, anomaly=anomaly, diagnosis=self.diagnoser.diagnose(anomaly), health=self.health.update(anomaly)))
        return out

    def train(self, features: list[FeatureRecord], dataset_id: str) -> None:
        trainable = self._complete(features)
        self.ml.fit(trainable, dataset_id)
        self.temporal_model.fit(trainable, dataset_id)

    def run(self, ingestion: IngestionResult, *, fit_ml: bool = True) -> IntelligenceResult:
        features = FoundationPipeline().run(ingestion).records
        return IntelligenceResult(dataset_id=ingestion.provenance.dataset_id, records=self.analyze(features, fit_ml=fit_ml, dataset_id=ingestion.provenance.dataset_id))
