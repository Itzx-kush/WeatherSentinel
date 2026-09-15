from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel,Field
class AnomalyStatus(StrEnum):NORMAL="NORMAL";ANOMALOUS="ANOMALOUS";UNCERTAIN="UNCERTAIN"
class Severity(StrEnum):NORMAL="NORMAL";LOW="LOW";MEDIUM="MEDIUM";HIGH="HIGH";CRITICAL="CRITICAL"
class DetectorEvidence(BaseModel):
 detector_name:str;detector_version:str="1.0.0";family:str;timestamp:datetime;station_id:str;affected_sensors:list[str]=Field(default_factory=list);raw_score:float|None=None;normalized_score:float|None=None;threshold:float|None=None;triggered:bool;reason:str;features:dict[str,Any]=Field(default_factory=dict);severity_contribution:float=Field(default=0,ge=0,le=1);sufficient_history:bool=True
class ModelMetadata(BaseModel):
 model_name:str;model_version:str;training_dataset_id:str;feature_version:str;preprocessing_version:str;random_seed:int;threshold:float;training_rows:int;configuration:dict[str,Any]
class AnomalyResult(BaseModel):
 timestamp:datetime;station_id:str;status:AnomalyStatus;anomaly_score:float=Field(ge=0,le=1);confidence:float=Field(ge=0,le=1);severity:Severity;affected_sensors:list[str];contributing_detectors:list[str];evidence:list[DetectorEvidence]
