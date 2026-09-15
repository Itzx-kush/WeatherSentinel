# WeatherSentinel

**SIH26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations**  
Ministry of Earth Sciences / India Meteorological Department · Disaster Management

WeatherSentinel is being built as a scientifically honest platform for distinguishing genuine meteorological behavior from sensor and communication failures using temperature, pressure, and relative humidity. This archive establishes the complete six-part architecture and fully implements **Part 1: Data Foundation & Weather Intelligence Core**. It does not claim anomaly detection, diagnosis, health scoring, an API, or a frontend yet.

## Implemented now

- Strict timezone-aware canonical AWS and station schemas
- Dataset provenance distinguishing real, synthetic, fault-injected, and unknown sources
- Bounded CSV and Parquet loaders with structured malformed-row errors
- Required-column, null, duplicate, physical-range, abrupt-change, freeze, and communication-gap checks
- Past-only rolling mean/median/std, lag, rate, trend, persistence, daily, and annual features
- Interpretable dew point, temperature–humidity interaction, and pressure-baseline context
- Reproducible Part 1 pipeline and timestamp-faithful replay with injectable timing
- Explicitly labelled synthetic example data and executable tests

## Architecture roadmap

1. **Implemented:** data foundation and weather intelligence
2. Detection: rule, statistical, ML, temporal, multivariate, fusion
3. Diagnosis: root cause, evidence, severity, health
4. Spatial and real-time: neighbors, regional-event reasoning, streaming
5. Correction and evaluation: immutable corrections, fault injection, benchmarks, edge path
6. Product: API, frontend, security, deployment, end-to-end SIH demo

Future capability directories are extension points only; no fabricated implementation or metrics are present.

## Windows setup

```powershell
cd D:\WeatherSentinel
.\scripts\setup.ps1
.\scripts\test.ps1
```

Process the included synthetic sample:

```powershell
.\.venv\Scripts\python.exe -m app.cli process `
  --input data\examples\aws_synthetic_normal.csv `
  --dataset-id imd-demo-synthetic-v1 `
  --source-type synthetic `
  --output data\processed\features.jsonl
```

Replay actual stored observations without waiting:

```powershell
.\scripts\replay-example.ps1 -Speed 0
```

For timestamp-scaled replay, use `-Speed 60` (ten minutes of source time becomes ten seconds). Replay never changes observation values.

## Data contract

CSV/Parquet columns are exactly:

`station_id,timestamp,temperature_c,pressure_hpa,relative_humidity_pct`

Timestamps must contain timezone offsets. Null sensor values are retained and flagged; malformed rows are retained as structured ingestion errors. Physical limits are configurable operational screening limits, not proof of sensor failure.

## Testing

The offline build environment ran Python compile checks, 14 standard-library unit/integration tests (13 passed, one Parquet test skipped because `pyarrow` was unavailable), real sample processing, and no-wait replay. See `docs/test-report.md`.

After setup on Windows, `scripts/test.ps1` runs compile checks, unittest discovery, and pytest when available. The project intentionally has no HTTP backend or frontend in Part 1.

## GitHub status

The connected GitHub token could read the repository but rejected writes with HTTP 403. This local archive is the current implementation source of truth. See `docs/github-workflow.md` for later synchronization.

## Limitations

- No anomaly detector or model performance claims yet
- No spatial reasoning, diagnosis, sensor health, correction, alerting, API, or UI yet
- Example observations are synthetic normal-weather data, not IMD measurements
- Parquet code exists but could not be exercised in the offline sandbox because `pyarrow` was unavailable
- Range and rate thresholds require calibration for climate, elevation, station hardware, and sampling interval

## License

MIT. See `LICENSE`.
