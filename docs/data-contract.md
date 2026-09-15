# Data contract

## Canonical observation v1

| Field | Type | Rule |
|---|---|---|
| `station_id` | string | non-empty, maximum 128 characters |
| `timestamp` | ISO-8601 datetime | timezone required; normalized to UTC |
| `temperature_c` | number/null | finite when present |
| `pressure_hpa` | number/null | finite when present |
| `relative_humidity_pct` | number/null | finite when present |

Null measurements are schema-valid so the quality layer can preserve and flag them. Missing columns, malformed timestamps, and non-numeric values become structured ingestion errors.

## Default screening limits

Temperature: -90–60 °C; pressure: 800–1100 hPa; humidity: 0–100%. These conservative defaults are screening rules, not meteorological truth for every deployment. Configuration must later be calibrated per network and elevation.

## Provenance

Each ingestion result records dataset ID, source filename, source type, UTC ingestion time, input record count, schema version, processing version, and optional seed. The included CSV is `synthetic`; it contains no injected fault or claimed real-world label.

## Feature leakage

For timestamp `t`, rolling statistics, lags, trend, and baseline use only accepted records before `t` from the same station. Invalid records do not enter future baselines. The current value is retained separately for deviation computation.
