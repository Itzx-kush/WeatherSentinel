# WeatherSentinel

SIH26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS).

WeatherSentinel is an end-to-end anomaly intelligence platform built around immutable AWS observations, past-only features, layered detection, explainable diagnosis, station/sensor health, spatial consistency, bounded correction, replay, evaluation, a FastAPI service, and a React dashboard.

## Architecture

`Observations → Quality → Past-only Features → Rule/Statistical/Temporal/Multivariate/IsolationForest → Evidence Fusion → Diagnosis → Health → Spatial Evidence → Correction Candidate → API/WebSocket → Frontend`

Raw observations remain immutable. Fault-injected datasets preserve provenance. Confidence represents evidence strength, not an unexplained probability. Corrections are proposed, validated, and auditable rather than silently overwriting source data.

## Current implementation

- Part 1: data foundation, ingestion, quality validation, past-only weather features, replay foundation
- Part 2: layered rule/statistical/temporal/multivariate detection, deterministic Isolation Forest, evidence fusion
- Part 3: root-cause diagnosis, severity, confidence, sensor/station health, deterministic fault injection and metrics
- Part 4: real-time event bus/WebSocket, station metadata, neighbor discovery and spatial peer consistency evidence
- Part 5: bounded correction candidates, validation/apply workflow, immutable raw observations, ground-truth-driven evaluation
- Part 6: product services, API contracts, frontend dashboard, replay/evaluation/system views
- Production backend: FastAPI, versioned routes, validation, OpenAPI, WebSocket events, Docker
- Frontend: React + TypeScript + Vite dashboard backed by live API endpoints
- CI: GitHub Actions for backend compile/tests/lint and frontend typecheck/build

## Backend

Install:

```powershell
python -m pip install -e ".[dev]"
```

Run:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

API docs are exposed by FastAPI at `/docs` and `/redoc`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_URL` when supplied and defaults to `http://localhost:8000`.

## Useful API routes

- `GET /health`
- `GET /api/v1/status`
- `POST /api/v1/stations/register`
- `POST /api/v1/observations/process`
- `POST /api/v1/datasets/process`
- `GET /api/v1/stations`
- `GET /api/v1/stations/{station_id}`
- `GET /api/v1/stations/{station_id}/anomalies`
- `GET /api/v1/stations/{station_id}/health`
- `GET /api/v1/stations/{station_id}/timeline`
- `POST /api/v1/replay`
- `POST /api/v1/evaluation/fault-injection`
- `GET /api/v1/evaluation/metrics`
- `GET /api/v1/corrections/{correction_id}`
- `POST /api/v1/corrections/{correction_id}/validate`
- `POST /api/v1/corrections/{correction_id}/apply`
- `GET /api/v1/spatial/stations`
- `GET /api/v1/spatial/{station_id}/neighbors`
- `GET /api/v1/models`
- `WS /api/v1/ws/events`

## Test commands

```powershell
.\scripts\setup.ps1
.\scripts\test.ps1
```

Frontend:

```powershell
cd frontend
npm install
npm run lint
npm run build
```

## Docker

```powershell
docker compose up --build
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:5173`

## Scientific/evaluation safeguards

The system keeps source observations immutable, separates truth labels from predictions, records detector evidence, carries model metadata, and exposes correction provenance. Evaluation metrics are computed from stored ground-truth/prediction pairs rather than from the prediction stream itself.

## Limitations

The current product layer uses an in-memory runtime store for development. A persistent repository implementation and authenticated deployment can be added without changing the domain contracts. The current frontend is intentionally lightweight and focuses on connecting real backend state rather than presenting synthetic demo values.
