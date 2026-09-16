from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from app.detection.contracts import DetectorEvidence, ModelMetadata
from app.schemas.models import FeatureRecord

SENSORS = ("temperature_c", "pressure_hpa", "relative_humidity_pct")


def _evidence(record: FeatureRecord, score: float | None, threshold: float, triggered: bool, reason: str, features: dict, enough: bool = True) -> DetectorEvidence:
    normalized = None if score is None else float(max(0.0, min(1.0, score)))
    return DetectorEvidence(
        detector_name="temporal_autoencoder",
        family="ml",
        timestamp=record.observation.timestamp,
        station_id=record.observation.station_id,
        affected_sensors=list(SENSORS),
        raw_score=score,
        normalized_score=normalized,
        threshold=threshold,
        triggered=triggered,
        reason=reason,
        features=features,
        severity_contribution=normalized or 0.0,
        sufficient_history=enough,
    )


@dataclass
class TemporalModelState:
    center: np.ndarray | None = None
    scale: np.ndarray | None = None
    components: np.ndarray | None = None
    error_scale: float | None = None
    threshold: float = 0.75
    training_windows: int = 0


class TemporalReconstructionDetector:
    """Learn normal multivariate temporal windows with a PCA reconstruction model."""

    model_name = "TemporalPCAAutoencoder"
    model_version = "1.0.0"
    feature_version = "aws-temporal-v1"
    preprocessing_version = "median-iqr-window-v1"

    def __init__(self, window_size: int = 12, components: int = 3, threshold: float = 0.75) -> None:
        if window_size < 4:
            raise ValueError("window_size must be at least 4")
        if components < 1 or components > window_size * len(SENSORS):
            raise ValueError("components must be within the flattened window dimension")
        self.window_size = window_size
        self.components = components
        self.threshold = threshold
        self.state = TemporalModelState(threshold=threshold)
        self.metadata: ModelMetadata | None = None
        self.history: dict[str, list[FeatureRecord]] = defaultdict(list)

    @staticmethod
    def vector(record: FeatureRecord) -> np.ndarray | None:
        values = [getattr(record.observation, sensor) for sensor in SENSORS]
        if any(value is None for value in values):
            return None
        return np.asarray(values, dtype=float)

    def _windows(self, records: list[FeatureRecord]) -> np.ndarray:
        grouped: dict[str, list[FeatureRecord]] = defaultdict(list)
        for record in records:
            if self.vector(record) is not None:
                grouped[record.observation.station_id].append(record)
        windows: list[np.ndarray] = []
        for rows in grouped.values():
            rows.sort(key=lambda x: x.observation.timestamp)
            vectors = [self.vector(row) for row in rows]
            for end in range(self.window_size - 1, len(vectors)):
                window = np.stack(vectors[end - self.window_size + 1 : end + 1])
                windows.append(window.reshape(-1))
        return np.asarray(windows, dtype=float) if windows else np.empty((0, self.window_size * len(SENSORS)))

    def fit(self, records: list[FeatureRecord], dataset_id: str) -> TemporalReconstructionDetector:
        windows = self._windows(records)
        if len(windows) < 8:
            raise ValueError("at least 8 complete temporal windows are required")

        center = np.median(windows, axis=0)
        q1, q3 = np.quantile(windows, [0.25, 0.75], axis=0)
        scale = np.maximum(q3 - q1, 1e-6)
        scaled = (windows - center) / scale
        mean = scaled.mean(axis=0, keepdims=True)
        centered = scaled - mean
        covariance = centered.T @ centered / max(len(scaled) - 1, 1)
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        order = np.argsort(eigenvalues)[::-1]
        k = min(self.components, centered.shape[1])
        components = eigenvectors[:, order[:k]].T
        reconstructed = centered @ components.T @ components + mean
        errors = np.mean((scaled - reconstructed) ** 2, axis=1)
        error_scale = float(max(np.quantile(errors, 0.95), 1e-6))

        self.state = TemporalModelState(
            center=center,
            scale=scale,
            components=components,
            error_scale=error_scale,
            threshold=self.threshold,
            training_windows=len(windows),
        )
        self.metadata = ModelMetadata(
            model_name=self.model_name,
            model_version=self.model_version,
            training_dataset_id=dataset_id,
            feature_version=self.feature_version,
            preprocessing_version=self.preprocessing_version,
            random_seed=26073,
            threshold=self.threshold,
            training_rows=len(records),
            configuration={
                "window_size": self.window_size,
                "components": k,
                "training_windows": len(windows),
                "error_scale": error_scale,
            },
        )
        self.history.clear()
        return self

    @property
    def fitted(self) -> bool:
        return self.state.components is not None

    def reset(self) -> None:
        self.history.clear()

    def _score_window(self, window: np.ndarray) -> tuple[float, float]:
        state = self.state
        scaled = (window.reshape(-1) - state.center) / state.scale
        projection = state.components.T @ (state.components @ scaled)
        error = float(np.mean((scaled - projection) ** 2))
        score = float(1.0 - np.exp(-error / state.error_scale))
        return score, error

    def detect(self, record: FeatureRecord) -> list[DetectorEvidence]:
        if not self.fitted:
            return [_evidence(record, None, self.threshold, False, "Temporal model not fitted", {}, False)]
        vector = self.vector(record)
        if vector is None:
            self.history[record.observation.station_id].clear()
            return [_evidence(record, None, self.threshold, False, "Incomplete temporal vector", {}, False)]

        station_history = self.history[record.observation.station_id]
        station_history.append(record)
        if len(station_history) < self.window_size:
            return [_evidence(record, None, self.threshold, False, "Insufficient temporal window", {"window_size": self.window_size, "history": len(station_history)}, False)]
        station_history[:] = station_history[-self.window_size :]
        window_vectors = [self.vector(row) for row in station_history]
        window = np.stack(window_vectors)
        score, error = self._score_window(window)
        triggered = score >= self.threshold
        return [_evidence(
            record,
            score,
            self.threshold,
            triggered,
            f"Temporal reconstruction score {score:.4f}",
            {
                "reconstruction_error": error,
                "window_size": self.window_size,
                "training_windows": self.state.training_windows,
                "model": self.metadata.model_dump(mode="json"),
            },
        )]
