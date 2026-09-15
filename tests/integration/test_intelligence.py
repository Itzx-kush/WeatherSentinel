import unittest
from datetime import UTC,datetime,timedelta
from app.schemas.models import AWSObservation,DatasetProvenance,IngestionResult,SourceType
from app.services.intelligence import IntelligenceService
from app.evaluation.faults import FaultType,inject
from app.detection.contracts import AnomalyStatus
from app.diagnosis.engine import RootCause
def rows(n=40):return [AWSObservation(station_id="S1",timestamp=datetime(2026,1,1,tzinfo=UTC)+timedelta(minutes=10*i),temperature_c=25+.1*(i%5),pressure_hpa=1005+.1*(i%3),relative_humidity_pct=70-.1*(i%4)) for i in range(n)]
def run(data,name):return IntelligenceService().run(IngestionResult(observations=data,errors=[],provenance=DatasetProvenance(dataset_id=name,source_filename="generated",source_type=SourceType.FAULT_INJECTED,record_count=len(data))))
class IntelligenceTests(unittest.TestCase):
 def test_normal(self):self.assertFalse(any(x.anomaly.status==AnomalyStatus.ANOMALOUS for x in run(rows(),"normal").records))
 def test_fault_scenarios(self):
  expected={FaultType.SPIKE:RootCause.SENSOR_SPIKE,FaultType.FREEZE:RootCause.SENSOR_FREEZE,FaultType.STEP_CHANGE:RootCause.SENSOR_STEP_CHANGE,FaultType.DROPOUT:RootCause.MISSING_DATA,FaultType.COMMUNICATION_GAP:RootCause.SENSOR_COMMUNICATION_GAP}
  for fault,cause in expected.items():
   data=inject(rows(),source_dataset_id="normal",dataset_id=fault.value,fault_type=fault,sensor="temperature_c",start=25,end=32,magnitude=30);out=run(data.observations,fault.value).records;self.assertTrue(any(x.anomaly.status==AnomalyStatus.ANOMALOUS for x in out));self.assertTrue(any(x.diagnosis.primary_root_cause==cause for x in out))
 def test_immutability(self):
  source=rows();before=[x.model_dump() for x in source];inject(source,source_dataset_id="n",dataset_id="f",fault_type=FaultType.DRIFT,sensor="temperature_c",start=20,end=25);self.assertEqual(before,[x.model_dump() for x in source])
