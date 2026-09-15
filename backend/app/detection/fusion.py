from app.detection.contracts import AnomalyResult,AnomalyStatus,Severity
DEFAULT_WEIGHTS={"rule":1.,"statistical":1.,"temporal":1.,"multivariate":1.,"ml":1.}
class FusionEngine:
 def __init__(self,weights=None,threshold=.5):self.weights=weights or DEFAULT_WEIGHTS.copy();self.threshold=threshold
 def fuse(self,evidence):
  if not evidence:raise ValueError("evidence required")
  first=evidence[0];available=[e for e in evidence if e.sufficient_history and e.normalized_score is not None and e.family in self.weights];families={}
  for e in available:families[e.family]=max(families.get(e.family,0),e.normalized_score)
  denom=sum(self.weights[x] for x in families);score=sum(self.weights[x]*v for x,v in families.items())/denom if denom else 0;hits=[e for e in evidence if e.triggered];hitfamilies={e.family for e in hits};hard=any(e.family=="rule" and e.severity_contribution>=.8 for e in hits);codes={e.features.get("code") for e in hits if e.family=="rule"};sensors={s for e in hits if e.family in {"statistical","temporal"} for s in e.affected_sensors};coherent=sensors==set(("temperature_c","pressure_hpa","relative_humidity_pct")) and not codes
  status=AnomalyStatus.NORMAL if coherent else AnomalyStatus.ANOMALOUS if hard or len(hitfamilies)>=2 or score>=self.threshold and hitfamilies else AnomalyStatus.UNCERTAIN if hits or len(families)<3 else AnomalyStatus.NORMAL;confidence=min(1,len(families)/len(self.weights)*(.5+.5*len(hitfamilies)/max(1,len(families))))
  severity=Severity.NORMAL if status==AnomalyStatus.NORMAL else Severity.CRITICAL if hard or score>=.85 else Severity.HIGH if score>=.7 else Severity.MEDIUM if score>=.5 else Severity.LOW
  return AnomalyResult(timestamp=first.timestamp,station_id=first.station_id,status=status,anomaly_score=score,confidence=confidence,severity=severity,affected_sensors=sorted({s for e in hits for s in e.affected_sensors}),contributing_detectors=sorted({e.detector_name for e in hits}),evidence=evidence)
