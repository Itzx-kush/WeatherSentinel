# Parts 2-3 methodology

WeatherSentinel emits structured evidence from quality rules, past-only rolling standardized deviation, stateful temporal patterns, diagonal multivariate distance, and an explicitly fitted deterministic isolation forest. ML fitting records dataset ID, preprocessing, feature version, seed, threshold, rows, and configuration; inference never silently fits.

Fusion uses configurable family weights. Anomaly score, evidence-strength confidence, and severity are separate. Status is NORMAL, UNCERTAIN, or ANOMALOUS. Confidence is detector coverage/agreement, not probability. All histories at time t contain only observations at or before t.
