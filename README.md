# WeatherSentinel

SIH26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations.

Parts 1-3 implement canonical ingestion and past-only weather features, layered rule/statistical/temporal/multivariate/unsupervised detection, explicit evidence fusion, uncertainty, diagnosis, severity, station and sensor health, deterministic fault injection, metrics, and intelligence replay.

Raw observations, synthetic/fault provenance, quality evidence, predictions, and diagnoses remain distinct. Confidence is evidence strength, not probability. Parts 4-6 and production API/frontend are not implemented.

## Windows testing

```powershell
cd D:\WeatherSentinel
.\scripts\setup.ps1
.\scripts\test.ps1
```
