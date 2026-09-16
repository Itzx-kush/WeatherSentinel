from __future__ import annotations

import math
from datetime import UTC, datetime
from pydantic import BaseModel, Field
from app.schemas.models import AWSObservation, StationMetadata

SENSORS = ("temperature_c", "pressure_hpa", "relative_humidity_pct")

class SpatialEvidence(BaseModel):
    station_id: str
    sensor: str
    neighbor_ids: list[str] = Field(default_factory=list)
    peer_value: float | None = None
    observed_value: float | None = None
    residual: float | None = None
    threshold: float | None = None
    triggered: bool = False
    reason: str

class SpatialAnalyzer:
    def __init__(self, stations: dict[str, StationMetadata], radius_km: float = 100.0, tolerance: dict[str,float] | None = None):
        self.stations = stations
        self.radius_km = radius_km
        self.tolerance = tolerance or {"temperature_c": 4.0, "pressure_hpa": 8.0, "relative_humidity_pct": 15.0}

    @staticmethod
    def distance_km(a: StationMetadata, b: StationMetadata) -> float | None:
        if a.latitude is None or b.latitude is None or a.longitude is None or b.longitude is None:
            return None
        r = 6371.0088
        p1, p2 = math.radians(a.latitude), math.radians(b.latitude)
        dp = math.radians(b.latitude - a.latitude)
        dl = math.radians(b.longitude - a.longitude)
        h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 2*r*math.asin(math.sqrt(h))

    def neighbors(self, station_id: str) -> list[str]:
        anchor = self.stations.get(station_id)
        if not anchor:
            return []
        out = []
        for sid, station in self.stations.items():
            if sid == station_id:
                continue
            d = self.distance_km(anchor, station)
            if d is not None and d <= self.radius_km:
                out.append(sid)
        return out

    def compare(self, observations: list[AWSObservation], observation: AWSObservation) -> list[SpatialEvidence]:
        peer_ids = set(self.neighbors(observation.station_id))
        peers = [r for r in observations if r.station_id in peer_ids and abs((r.timestamp-observation.timestamp).total_seconds()) <= 900]
        result = []
        for sensor in SENSORS:
            value = getattr(observation, sensor)
            values = [getattr(r, sensor) for r in peers if getattr(r, sensor) is not None]
            if value is None or not values:
                result.append(SpatialEvidence(station_id=observation.station_id, sensor=sensor, neighbor_ids=sorted({r.station_id for r in peers}), observed_value=value, reason="Insufficient peer observations"))
                continue
            peer = sum(values) / len(values)
            residual = value - peer
            threshold = self.tolerance[sensor]
            result.append(SpatialEvidence(station_id=observation.station_id, sensor=sensor, neighbor_ids=sorted({r.station_id for r in peers}), peer_value=peer, observed_value=value, residual=residual, threshold=threshold, triggered=abs(residual) >= threshold, reason=f"Peer residual {residual:.3f} against tolerance {threshold:.3f}"))
        return result
