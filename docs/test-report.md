# Part 1 test report

**Date:** 2026-09-15  
**Environment:** isolated Linux sandbox used to build the Windows-ready archive  
**Python:** 3.13.14  
**Pydantic:** 2.13.5  
**Pandas:** 3.0.5  
**Node/frontend:** not applicable; frontend is intentionally not implemented in Part 1

## Commands and actual results

1. `PYTHONPATH=backend python3 -m compileall -q backend tests` — passed.
2. `PYTHONPATH=backend python3 -m unittest discover -s tests -t . -p 'test_*.py' -v` — 14 tests discovered; 13 passed; 1 skipped; 0 failed.
3. `PYTHONPATH=backend python3 -m app.cli process --input data/examples/aws_synthetic_normal.csv --dataset-id imd-demo-synthetic-v1 --source-type synthetic --output data/processed/features.jsonl` — passed; 12 records processed; 12 valid; 0 suspect; 0 invalid; 0 malformed.
4. `PYTHONPATH=backend python3 -m app.cli replay --input data/examples/aws_synthetic_normal.csv --dataset-id imd-demo-synthetic-v1 --source-type synthetic --speed 0` — passed; 12 source observations emitted unchanged and in timestamp order.
5. Integration assertions verified 12 feature rows, 12 replay rows, preserved first temperature value, expected station ID, and a prior-only rolling mean of 27.1 for the second record — passed.

## Coverage exercised

Canonical schema acceptance and rejection; UTC normalization; station metadata; valid/malformed/missing-column CSV; null/range/duplicate/freeze/gap quality flags; temporal and multivariate features; future-leakage prevention; deterministic output; replay ordering, timing abstraction and value preservation; complete sample pipeline; structured malformed-record handling.

## Skipped and unavailable checks

- Parquet round-trip test skipped because `pyarrow` was not installed in the offline sandbox. The loader and Windows dependency declaration are present; run `scripts/test.ps1` after `scripts/setup.ps1` on Windows to execute it.
- `pytest`, `ruff`, and `pyarrow` could not be installed because outbound package-network access was unavailable. The standard-library unittest suite was executed instead. These tools remain declared in the development dependencies for the target Windows environment.

## Backend and frontend status

Part 1 is a Python library and CLI. No HTTP backend was created, so no server startup or endpoint claim applies. The frontend is an architectural directory only and was not built or started.

## Completion status

Part 1 data foundation is implemented and its available core checks passed. Parquet runtime verification remains pending in an environment with `pyarrow`. Parts 2–6 are architectural extension points only.
