from pydantic import BaseModel
from app.detection.contracts import AnomalyResult
from app.detection.detectors import MultivariateDetector,RuleDetector,StatisticalDetector,TemporalDetector
from app.detection.fusion import FusionEngine
from app.diagnosis.engine import Diagnosis,DiagnosisEngine
from app.health.tracker import HealthSnapshot,HealthTracker
from app.schemas.models import FeatureRecord,IngestionResult
from app.services.pipeline import FoundationPipeline
class IntelligenceRecord(BaseModel):feature_record:FeatureRecord;anomaly:AnomalyResult;diagnosis:Diagnosis;health:HealthSnapshot
class IntelligenceResult(BaseModel):dataset_id:str;records:list[IntelligenceRecord]
class IntelligenceService:
 def __init__(self,ml=None):self.detectors=[RuleDetector(),StatisticalDetector(),TemporalDetector(),MultivariateDetector()]+([ml] if ml else []);self.fusion=FusionEngine();self.diagnoser=DiagnosisEngine();self.health=HealthTracker()
 def analyze(self,features):
  out=[]
  for r in features:
   evidence=[]
   for detector in self.detectors:evidence.extend(detector.detect(r))
   anomaly=self.fusion.fuse(evidence);out.append(IntelligenceRecord(feature_record=r,anomaly=anomaly,diagnosis=self.diagnoser.diagnose(anomaly),health=self.health.update(anomaly)))
  return out
 def run(self,ingestion:IngestionResult):return IntelligenceResult(dataset_id=ingestion.provenance.dataset_id,records=self.analyze(FoundationPipeline().run(ingestion).records))
