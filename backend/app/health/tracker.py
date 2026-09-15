from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel,Field
from app.detection.contracts import AnomalyStatus,Severity
SENSORS=("temperature_c","pressure_hpa","relative_humidity_pct")
class HealthState(StrEnum):HEALTHY="HEALTHY";WARNING="WARNING";DEGRADED="DEGRADED";CRITICAL="CRITICAL";UNKNOWN="UNKNOWN"
class HealthSnapshot(BaseModel):station_id:str;score:float;state:HealthState;per_sensor_scores:dict[str,float]=Field(default_factory=dict);recent_anomaly_count:int;observations:int;last_healthy_observation:datetime|None=None;last_anomalous_observation:datetime|None=None;evidence_trend:float
class HealthTracker:
 burden={Severity.NORMAL:0.,Severity.LOW:.25,Severity.MEDIUM:.5,Severity.HIGH:.75,Severity.CRITICAL:1.}
 def __init__(self,window=12):self.window=window;self.rows={}
 def update(self,a):
  rows=self.rows.setdefault(a.station_id,[]);rows.append((a.timestamp,a.status,a.severity,tuple(a.affected_sensors)));del rows[:-self.window];values=[self.burden[s] for _,_,s,_ in rows];score=100*(1-sum(values)/len(values));sensor_scores={s:100*(1-sum(self.burden[v] if s in affected else 0 for _,_,v,affected in rows)/len(rows)) for s in SENSORS};bad=[t for t,status,_,_ in rows if status==AnomalyStatus.ANOMALOUS];good=[t for t,status,_,_ in rows if status==AnomalyStatus.NORMAL];state=HealthState.UNKNOWN if len(rows)<3 else HealthState.HEALTHY if score>=85 else HealthState.WARNING if score>=65 else HealthState.DEGRADED if score>=40 else HealthState.CRITICAL;half=max(1,len(values)//2);trend=sum(values[-half:])/len(values[-half:])-sum(values[:half])/len(values[:half]);return HealthSnapshot(station_id=a.station_id,score=score,state=state,per_sensor_scores=sensor_scores,recent_anomaly_count=len(bad),observations=len(rows),last_healthy_observation=good[-1] if good else None,last_anomalous_observation=bad[-1] if bad else None,evidence_trend=trend)
