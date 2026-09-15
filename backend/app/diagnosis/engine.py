from enum import StrEnum
from pydantic import BaseModel,Field
from app.detection.contracts import AnomalyStatus,Severity
class RootCause(StrEnum):
 NORMAL_WEATHER_EVENT="NORMAL_WEATHER_EVENT";SENSOR_OUT_OF_RANGE="SENSOR_OUT_OF_RANGE";SENSOR_SPIKE="SENSOR_SPIKE";SENSOR_FREEZE="SENSOR_FREEZE";SENSOR_DRIFT="SENSOR_DRIFT";SENSOR_STEP_CHANGE="SENSOR_STEP_CHANGE";SENSOR_BIAS="SENSOR_BIAS";SENSOR_COMMUNICATION_GAP="SENSOR_COMMUNICATION_GAP";MISSING_DATA="MISSING_DATA";MULTI_SENSOR_INCONSISTENCY="MULTI_SENSOR_INCONSISTENCY";UNKNOWN="UNKNOWN"
class Diagnosis(BaseModel):
 primary_root_cause:RootCause;alternative_causes:list[RootCause]=Field(default_factory=list);evidence:list[str];affected_sensors:list[str];severity:Severity;confidence:float;explanation:str;detector_contributions:list[str]
class DiagnosisEngine:
 def diagnose(self,a):
  codes={e.features.get("code") for e in a.evidence if e.triggered};patterns={e.features.get("pattern") for e in a.evidence if e.triggered and e.family=="temporal"};multi=any(e.triggered and e.family=="multivariate" for e in a.evidence)
  if "missing_value" in codes:c=RootCause.MISSING_DATA
  elif "communication_gap" in codes:c=RootCause.SENSOR_COMMUNICATION_GAP
  elif "physical_range" in codes:c=RootCause.SENSOR_OUT_OF_RANGE
  elif "frozen_value" in codes or "freeze" in patterns:c=RootCause.SENSOR_FREEZE
  elif a.status==AnomalyStatus.NORMAL:c=RootCause.NORMAL_WEATHER_EVENT
  elif "step" in patterns:c=RootCause.SENSOR_STEP_CHANGE
  elif "drift" in patterns:c=RootCause.SENSOR_DRIFT
  elif "bias" in patterns:c=RootCause.SENSOR_BIAS
  elif "abrupt" in patterns:c=RootCause.SENSOR_SPIKE
  elif multi and len(a.affected_sensors)==1:c=RootCause.MULTI_SENSOR_INCONSISTENCY
  else:c=RootCause.UNKNOWN
  alternatives={RootCause.SENSOR_SPIKE:[RootCause.SENSOR_STEP_CHANGE],RootCause.SENSOR_STEP_CHANGE:[RootCause.SENSOR_BIAS,RootCause.SENSOR_DRIFT],RootCause.SENSOR_DRIFT:[RootCause.SENSOR_BIAS],RootCause.MULTI_SENSOR_INCONSISTENCY:[RootCause.UNKNOWN]}.get(c,[]);reasons=[e.reason for e in a.evidence if e.triggered];confidence=a.confidence if c!=RootCause.UNKNOWN else min(a.confidence,.5)
  return Diagnosis(primary_root_cause=c,alternative_causes=alternatives,evidence=reasons,affected_sensors=a.affected_sensors,severity=a.severity,confidence=confidence,explanation=f"{c.value} derived from {len(reasons)} triggered evidence item(s)",detector_contributions=a.contributing_detectors)
