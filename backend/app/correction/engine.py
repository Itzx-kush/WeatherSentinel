from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field
from app.schemas.models import AWSObservation

class CorrectionStatus(StrEnum):
    REJECTED = "rejected"
    SUGGESTED = "suggested"
    VALIDATED = "validated"
    APPLIED = "applied"

class CorrectionCandidate(BaseModel):
    correction_id: str
    station_id: str
    sensor: str
    timestamp: datetime
    original_value: float | None
    corrected_value: float | None
    method: str
    confidence: float = Field(ge=0, le=1)
    uncertainty: float | None = None
    evidence: list[str] = Field(default_factory=list)
    status: CorrectionStatus = CorrectionStatus.SUGGESTED
    model_version: str = "correction-v1"

class CorrectionEngine:
    def __init__(self, physical_bounds: dict[str, tuple[float,float]] | None = None):
        self.bounds = physical_bounds or {
            "temperature_c": (-80.0, 65.0),
            "pressure_hpa": (800.0, 1200.0),
            "relative_humidity_pct": (0.0, 100.0),
        }

    def propose(self, observation: AWSObservation, sensor: str, *, temporal_value: float | None = None, peer_value: float | None = None, baseline_value: float | None = None, trigger: str = "") -> CorrectionCandidate | None:
        original = getattr(observation, sensor)
        candidates = [("temporal", temporal_value), ("spatial_peer", peer_value), ("baseline", baseline_value)]
        candidates = [(m, v) for m, v in candidates if v is not None]
        if not candidates:
            return None
        values = [v for _, v in candidates]
        corrected = sum(values) / len(values)
        lo, hi = self.bounds[sensor]
        evidence = [f"source:{m}" for m, _ in candidates]
        evidence.append(f"trigger:{trigger or 'unspecified'}")
        if corrected < lo or corrected > hi:
            return CorrectionCandidate(correction_id=f"{observation.station_id}:{sensor}:{observation.timestamp.isoformat()}", station_id=observation.station_id, sensor=sensor, timestamp=observation.timestamp, original_value=original, corrected_value=None, method="bounded_consensus", confidence=0, evidence=evidence+["physical_bounds_failed"], status=CorrectionStatus.REJECTED)
        spread = max(values)-min(values) if len(values)>1 else 0.0
        confidence = max(0.0, min(1.0, 1.0 - spread / max(abs(corrected)*0.1, 1.0)))
        return CorrectionCandidate(correction_id=f"{observation.station_id}:{sensor}:{observation.timestamp.isoformat()}", station_id=observation.station_id, sensor=sensor, timestamp=observation.timestamp, original_value=original, corrected_value=corrected, method="bounded_consensus", confidence=confidence, uncertainty=spread, evidence=evidence)

    @staticmethod
    def validate(candidate: CorrectionCandidate, minimum_confidence: float = 0.65) -> CorrectionCandidate:
        if candidate.corrected_value is None or candidate.confidence < minimum_confidence or candidate.status == CorrectionStatus.REJECTED:
            return candidate.model_copy(update={"status": CorrectionStatus.REJECTED})
        return candidate.model_copy(update={"status": CorrectionStatus.VALIDATED})
