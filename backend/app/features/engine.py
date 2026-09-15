"""Leakage-safe temporal/statistical and physically interpretable multivariate features."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict, deque

from pydantic import BaseModel, Field

from app.schemas.models import FeatureRecord, QualityStatus, ValidatedRecord

SENSORS = ("temperature_c", "pressure_hpa", "relative_humidity_pct")


class FeatureConfig(BaseModel):
    rolling_window: int = Field(default=12, ge=3)
    lags: tuple[int, ...] = (1, 3, 6)


class FeatureEngine:
    def __init__(self, config=None):
        self.config = config or FeatureConfig()

    @staticmethod
    def _slope(values):
        if len(values) < 2:
            return None
        xm = (len(values) - 1) / 2
        ym = statistics.fmean(values)
        den = sum((i - xm) ** 2 for i in range(len(values)))
        return sum((i - xm) * (v - ym) for i, v in enumerate(values)) / den

    @staticmethod
    def _dew_point(t, h):
        if t is None or h is None or h <= 0:
            return None
        a, b = 17.625, 243.04
        gamma = math.log(h / 100) + a * t / (b + t)
        return b * gamma / (a - gamma)

    def transform(self, records: list[ValidatedRecord]) -> list[FeatureRecord]:
        history = defaultdict(lambda: deque(maxlen=self.config.rolling_window))
        persistence = {}
        out = []
        for item in sorted(
            records, key=lambda x: (x.observation.station_id, x.observation.timestamp)
        ):
            row = item.observation
            temporal = {}
            baseline = {}
            for sensor in SENSORS:
                values = list(history[(row.station_id, sensor)])
                current = getattr(row, sensor)
                mean = statistics.fmean(values) if values else None
                median = statistics.median(values) if values else None
                std = statistics.stdev(values) if len(values) >= 2 else None
                latest = values[-1] if values else None
                old = persistence.get((row.station_id, sensor))
                count = (
                    old[1] + 1
                    if current is not None and old and current == old[0]
                    else (1 if current is not None else 0)
                )
                temporal[sensor] = {
                    "rolling_mean": mean,
                    "rolling_median": median,
                    "rolling_std": std,
                    "local_deviation": current - median
                    if current is not None and median is not None
                    else None,
                    "rate_of_change": current - latest
                    if current is not None and latest is not None
                    else None,
                    "trend_slope": self._slope(values),
                    "persistence_count": count,
                    **{
                        f"lag_{lag}": values[-lag] if len(values) >= lag else None
                        for lag in self.config.lags
                    },
                }
                baseline[sensor] = median
                if current is not None:
                    persistence[(row.station_id, sensor)] = (current, count)
                    if item.status != QualityStatus.INVALID:
                        history[(row.station_id, sensor)].append(current)
            hour = row.timestamp.hour + row.timestamp.minute / 60
            day = row.timestamp.timetuple().tm_yday
            t = row.temperature_c
            h = row.relative_humidity_pct
            pbase = baseline["pressure_hpa"]
            multi = {
                "dew_point_c": self._dew_point(t, h),
                "temperature_humidity_interaction": t * h / 100
                if t is not None and h is not None
                else None,
                "pressure_baseline_deviation": row.pressure_hpa - pbase
                if row.pressure_hpa is not None and pbase is not None
                else None,
                "hour_sin": math.sin(2 * math.pi * hour / 24),
                "hour_cos": math.cos(2 * math.pi * hour / 24),
                "day_of_year_sin": math.sin(2 * math.pi * day / 365.25),
                "day_of_year_cos": math.cos(2 * math.pi * day / 365.25),
            }
            out.append(
                FeatureRecord(
                    observation=row,
                    quality_status=item.status,
                    quality_flags=item.flags,
                    temporal_features=temporal,
                    multivariate_features=multi,
                    normal_baseline=baseline,
                )
            )
        return out
