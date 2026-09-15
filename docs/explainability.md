# Explainability and health

Diagnosis is evidence-driven and supports NORMAL_WEATHER_EVENT, SENSOR_OUT_OF_RANGE, SENSOR_SPIKE, SENSOR_FREEZE, SENSOR_DRIFT, SENSOR_STEP_CHANGE, SENSOR_BIAS, SENSOR_COMMUNICATION_GAP, MISSING_DATA, MULTI_SENSOR_INCONSISTENCY, and UNKNOWN. Outputs retain alternatives, reasons, sensors, severity, confidence, and detector contributions.

Station health is `100 * (1 - mean(recent severity burdens))`, where NORMAL=0, LOW=.25, MEDIUM=.5, HIGH=.75, CRITICAL=1. Per-sensor scores apply burden only when that sensor is affected. Health is evidence summary, not failure probability.
