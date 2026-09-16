from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from app.api.schemas import CorrectionActionRequest, FaultInjectionRequest, ProcessRequest, StationRegistrationRequest, StatusResponse
from app.evaluation.faults import FaultType, inject
from app.spatial.engine import SpatialAnalyzer

router = APIRouter()

def runtime(request: Request):
    return request.app.state.runtime

@router.get("/health")
async def health(request: Request):
    rt = runtime(request)
    return {"status": "ok", "service": "weathersentinel", "version": request.app.state.version, "stations": len(rt.stations), "observations": len(rt.observations)}

@router.get("/api/v1/status", response_model=StatusResponse)
async def status(request: Request):
    return StatusResponse(service="weathersentinel", version=request.app.state.version, status="ready", timestamp=datetime.now(UTC))

@router.post("/api/v1/stations/register")
async def register_stations(body: StationRegistrationRequest, request: Request):
    runtime(request).register_stations(body.stations)
    return {"registered": len(body.stations), "stations": [s.station_id for s in body.stations]}

@router.get("/api/v1/stations")
async def list_stations(request: Request):
    rt = runtime(request)
    ids = set(rt.stations) | {o.station_id for o in rt.observations}
    return {"stations": [rt.station_summary(s) for s in sorted(ids)]}

@router.get("/api/v1/stations/{station_id}/sensors")
async def sensors(station_id: str, request: Request):
    rt = runtime(request)
    latest = next((o for o in reversed(rt.observations) if o.station_id == station_id), None)
    if latest is None:
        raise HTTPException(404, "station has no observations")
    health = rt.health.get(station_id)
    return {"station_id": station_id, "values": latest.model_dump(mode="json"), "health": health.model_dump(mode="json") if health else None}

@router.get("/api/v1/stations/{station_id}/anomalies")
async def anomalies(station_id: str, request: Request):
    return {"station_id": station_id, "anomalies": [a for a in runtime(request).anomalies if a["station_id"] == station_id]}

@router.get("/api/v1/stations/{station_id}/health")
async def station_health(station_id: str, request: Request):
    health = runtime(request).health.get(station_id)
    if health is None:
        raise HTTPException(404, "health not available")
    return health

@router.get("/api/v1/stations/{station_id}/timeline")
async def timeline(station_id: str, request: Request):
    return {"station_id": station_id, "events": [e for e in runtime(request).events if e.get("station_id") == station_id]}

@router.get("/api/v1/stations/{station_id}")
async def station(station_id: str, request: Request):
    rt = runtime(request)
    if station_id not in rt.stations and not any(o.station_id == station_id for o in rt.observations):
        raise HTTPException(404, "station not found")
    return rt.station_summary(station_id)

@router.post("/api/v1/observations/process")
async def process(body: ProcessRequest, request: Request):
    return {"dataset_id": body.dataset_id, "results": await runtime(request).process(body.observations, body.dataset_id)}

@router.post("/api/v1/datasets/process")
async def process_dataset(body: ProcessRequest, request: Request):
    return {"dataset_id": body.dataset_id, "results": await runtime(request).process(body.observations, body.dataset_id)}

@router.post("/api/v1/replay")
async def replay(body: ProcessRequest, request: Request):
    replay_id = str(uuid4())
    results = await runtime(request).process(body.observations, body.dataset_id)
    runtime(request).replays[replay_id] = {"replay_id": replay_id, "dataset_id": body.dataset_id, "created_at": datetime.now(UTC).isoformat(), "results": results}
    return runtime(request).replays[replay_id]

@router.get("/api/v1/replay/{replay_id}")
async def get_replay(replay_id: str, request: Request):
    replay = runtime(request).replays.get(replay_id)
    if not replay:
        raise HTTPException(404, "replay not found")
    return replay

@router.post("/api/v1/evaluation/fault-injection")
async def fault_injection(body: FaultInjectionRequest, request: Request):
    rt = runtime(request)
    if not rt.observations:
        raise HTTPException(400, "process baseline observations before fault injection")
    try:
        injected = inject(rt.observations, source_dataset_id="runtime", dataset_id=f"fault-{uuid4()}", fault_type=FaultType(body.fault_type), sensor=body.sensor, start=body.start, end=body.end, magnitude=body.magnitude, station_id=body.station_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(400, str(exc)) from exc
    results = await rt.process(injected.observations, injected.metadata.dataset_id, truth_labels=injected.labels)
    return {"metadata": injected.metadata.model_dump(mode="json"), "labels": injected.labels, "results": results}

@router.post("/api/v1/evaluation/run")
async def evaluation_run(request: Request):
    return runtime(request).metrics()

@router.get("/api/v1/evaluation/metrics")
async def evaluation_metrics(request: Request):
    return runtime(request).metrics()

@router.get("/api/v1/anomalies/{anomaly_id}")
async def anomaly(anomaly_id: str, request: Request):
    for item in runtime(request).anomalies:
        if f"{item['station_id']}:{item['timestamp']}" == anomaly_id:
            return item
    raise HTTPException(404, "anomaly not found")

@router.get("/api/v1/diagnoses/{diagnosis_id}")
async def diagnosis(diagnosis_id: str, request: Request):
    item = next((a for a in runtime(request).anomalies if f"{a['station_id']}:{a['timestamp']}" == diagnosis_id), None)
    if not item:
        raise HTTPException(404, "diagnosis not found")
    return item["diagnosis"]

@router.get("/api/v1/corrections/{correction_id}")
async def correction(correction_id: str, request: Request):
    item = runtime(request).corrections.get(correction_id)
    if not item:
        raise HTTPException(404, "correction not found")
    return item

@router.post("/api/v1/corrections/{correction_id}/validate")
async def validate_correction(correction_id: str, body: CorrectionActionRequest, request: Request):
    rt = runtime(request)
    item = rt.corrections.get(correction_id)
    if not item:
        raise HTTPException(404, "correction not found")
    validated = rt.correction.validate(item, body.minimum_confidence)
    rt.corrections[correction_id] = validated
    return validated

@router.post("/api/v1/corrections/{correction_id}/apply")
async def apply_correction(correction_id: str, request: Request):
    rt = runtime(request)
    item = rt.corrections.get(correction_id)
    if not item or item.status.value != "validated":
        raise HTTPException(409, "correction must be validated before application")
    applied = item.model_copy(update={"status": "applied"})
    rt.corrections[correction_id] = applied
    await rt.bus.publish({"type": "correction_applied", "correction": applied.model_dump(mode="json")})
    return applied

@router.get("/api/v1/spatial/stations")
async def spatial_stations(request: Request):
    return {"stations": [s.model_dump(mode="json") for s in runtime(request).stations.values()]}

@router.get("/api/v1/spatial/{station_id}/neighbors")
async def neighbors(station_id: str, request: Request):
    rt = runtime(request)
    return {"station_id": station_id, "neighbors": SpatialAnalyzer(rt.stations).neighbors(station_id)}

@router.get("/api/v1/models")
async def models(request: Request):
    rt = runtime(request)
    return {"models": [{"name": "IsolationForest", "version": "1.0.0", "integrated": any(type(d).__name__ == "IsolationForestDetector" for d in rt.intelligence.detectors)}, {"name": "rule/statistical/temporal/multivariate", "version": "1.0.0", "integrated": True}]}

@router.get("/api/v1/system/config")
async def config(request: Request):
    return {"version": request.app.state.version, "features": {"spatial": True, "realtime": True, "correction": True, "fault_injection": True, "replay": True}}

@router.websocket("/api/v1/ws/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    rt = websocket.app.state.runtime
    try:
        async for event in rt.bus.subscribe():
            await websocket.send_json(event)
    except WebSocketDisconnect:
        return
