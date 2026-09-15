# Architecture

## Design rule

The architecture is stable across all six implementation parts; capabilities are added behind explicit module boundaries rather than restructuring the repository every cycle.

```text
Observation → ingestion → quality → feature engine
            → detection → fusion → spatial reasoning
            → diagnosis/explanation → sensor health
            → alert/correction → evaluation → API/UI
```

## Implemented Part 1 boundaries

- `schemas`: immutable input contracts and distinct output contracts
- `data`: file loaders, provenance, and deterministic quality evidence
- `features`: past-only temporal/statistical features and defensible cross-sensor context
- `services`: orchestration without HTTP or model concerns
- `replay`: preserves record values and uses source timestamp deltas

## Prepared extension points

`detection`, `diagnosis`, `explainability`, `spatial`, `health`, `correction`, `evaluation`, `edge`, `api`, `frontend`, `models`, and `deployment` are represented as directories. They deliberately contain no fake detectors, endpoints, dashboards, or metrics. Their contracts will be introduced with the corresponding part.

## Scientific safeguards

Raw observations are never overwritten by features or future corrections. Dataset provenance records source type. Current rows are excluded from their own rolling baseline, preventing look-ahead leakage. Quality flags are evidence, not ground-truth anomaly labels.
