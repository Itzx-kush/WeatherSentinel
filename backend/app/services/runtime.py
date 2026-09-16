from __future__ import annotations

from app.correction.engine import CorrectionCandidate, CorrectionEngine
from app.evaluation.metrics import detection_metrics
from app.health.tracker import HealthSnapshot
from app.realtime.bus import EventBus
from app.schemas.models import AWSObservation, DatasetProvenance, IngestionResult, SourceType, StationMetadata
from app.services.intelligence import IntelligenceService
from app.spatial.engine import SpatialAnalyzer

class RuntimeStore:
    def __init__(self):
        self.observations: list[AWSObservation] = []
        self.anomalies: list[dict] = []
        self.diagnoses: list[dict] = []
        self.health: dict[str, HealthSnapshot] = {}
        self.stations: dict[str, StationMetadata] = {}
        self.corrections: dict[str, CorrectionCandidate] = {}
        self.replays: dict[str, dict] = {}
        self.events: list[dict] = []
        self.evaluation_pairs: list[tuple[bool, bool]] = []
        self.bus = EventBus()
        self.intelligence = IntelligenceService()
        self.correction = CorrectionEngine()

    def register_stations(self, stations: list[StationMetadata]) -> None:
        self.stations.update({s.station_id: s for s in stations})

    def _ingestion(self, observations: list[AWSObservation], dataset_id: str = "runtime") -> IngestionResult:
        p = DatasetProvenance(dataset_id=dataset_id, source_filename="api", source_type=SourceType.REAL, record_count=len(observations), processing_version="part6-1.0.0")
        return IngestionResult(observations=observations, errors=[], provenance=p)

    async def process(self, observations: list[AWSObservation], dataset_id: str = "runtime", truth_labels: list[bool] | None = None) -> list[dict]:
        if not observations:
            return []
        self.observations.extend(observations)
        result = self.intelligence.run(self._ingestion(observations, dataset_id))
        spatial = SpatialAnalyzer(self.stations)
        out = []
        labels = truth_labels if truth_labels is not None else [False] * len(result.records)
        if len(labels) != len(result.records):
            raise ValueError("truth_labels must align with processed records")
        for idx, record in enumerate(result.records):
            a = record.anomaly
            d = record.diagnosis
            h = record.health
            spatial_evidence = spatial.compare(self.observations, record.feature_record.observation)
            payload = {"timestamp": a.timestamp.isoformat(), "station_id": a.station_id, "anomaly": a.model_dump(mode="json"), "diagnosis": d.model_dump(mode="json"), "health": h.model_dump(mode="json"), "spatial": [x.model_dump(mode="json") for x in spatial_evidence], "spatial_anomaly": any(x.triggered for x in spatial_evidence)}
            self.anomalies.append(payload)
            self.diagnoses.append(payload["diagnosis"])
            self.health[a.station_id] = h
            self.evaluation_pairs.append((bool(labels[idx]), a.status.value == "ANOMALOUS"))
            self.events.append({"type": "analysis", **payload})
            await self.bus.publish({"type": "analysis", **payload})
            if a.affected_sensors:
                sensor = a.affected_sensors[0]
                peer = next((x.peer_value for x in spatial_evidence if x.sensor == sensor and x.peer_value is not None), None)
                baseline = record.feature_record.normal_baseline.get(sensor)
                candidate = self.correction.propose(record.feature_record.observation, sensor, peer_value=peer, baseline_value=baseline, trigger=d.primary_root_cause.value)
                if candidate:
                    self.corrections[candidate.correction_id] = candidate
                    payload["correction"] = candidate.model_dump(mode="json")
                    await self.bus.publish({"type": "correction", **payload})
            out.append(payload)
        return out

    def station_summary(self, station_id: str) -> dict:
        station = self.stations.get(station_id)
        obs = [o for o in self.observations if o.station_id == station_id]
        anomalies = [a for a in self.anomalies if a["station_id"] == station_id]
        return {"station": station.model_dump(mode="json") if station else {"station_id": station_id}, "observations": len(obs), "latest_observation": obs[-1].model_dump(mode="json") if obs else None, "health": self.health.get(station_id).model_dump(mode="json") if station_id in self.health else None, "active_anomalies": [a for a in anomalies[-20:] if a["anomaly"]["status"] == "ANOMALOUS"]}

    def metrics(self) -> dict:
        if not self.evaluation_pairs:
            return {"status": "no_evaluation_data"}
        truth, pred = zip(*self.evaluation_pairs)
        metrics = detection_metrics(list(truth), list(pred)).model_dump()
        metrics["evaluated_records"] = len(self.evaluation_pairs)
        return metrics
