"""Deterministic quality checks producing evidence, never ML labels."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.models import (
    AWSObservation,
    FlagLevel,
    QualityFlag,
    QualityStatus,
    ValidatedRecord,
)

SENSORS = ("temperature_c", "pressure_hpa", "relative_humidity_pct")


class QualityConfig(BaseModel):
    expected_interval_seconds: int = Field(default=600, gt=0)
    gap_multiplier: float = Field(default=1.5, gt=1)
    freeze_consecutive: int = Field(default=4, ge=2)
    freeze_tolerance: float = Field(default=1e-9, ge=0)
    physical_ranges: dict[str, tuple[float, float]] = Field(
        default_factory=lambda: {
            "temperature_c": (-90, 60),
            "pressure_hpa": (800, 1100),
            "relative_humidity_pct": (0, 100),
        }
    )
    max_change_per_interval: dict[str, float] = Field(
        default_factory=lambda: {
            "temperature_c": 12,
            "pressure_hpa": 12,
            "relative_humidity_pct": 45,
        }
    )


class QualityValidator:
    def __init__(self, config=None):
        self.config = config or QualityConfig()

    def validate(self, observations: list[AWSObservation]) -> list[ValidatedRecord]:
        ordered = sorted(
            enumerate(observations), key=lambda p: (p[1].station_id, p[1].timestamp, p[0])
        )
        seen = set()
        previous = {}
        repeated = {}
        out = []
        for _, row in ordered:
            flags = []
            key = (row.station_id, row.timestamp)
            if key in seen:
                flags.append(
                    QualityFlag(
                        code="duplicate_timestamp",
                        level=FlagLevel.ERROR,
                        field="timestamp",
                        message="Duplicate station timestamp",
                        observed=row.timestamp.isoformat(),
                    )
                )
            seen.add(key)
            prior = previous.get(row.station_id)
            if prior:
                elapsed = (row.timestamp - prior.timestamp).total_seconds()
                expected = self.config.expected_interval_seconds
                if elapsed > expected * self.config.gap_multiplier:
                    flags.append(
                        QualityFlag(
                            code="communication_gap",
                            level=FlagLevel.WARNING,
                            field="timestamp",
                            message=(
                                f"Approximately {max(0, round(elapsed / expected) - 1)} "
                                "interval(s) absent"
                            ),
                            observed=elapsed,
                            expected=f"approximately {expected} seconds",
                        )
                    )
            for sensor in SENSORS:
                value = getattr(row, sensor)
                if value is None:
                    flags.append(
                        QualityFlag(
                            code="missing_value",
                            level=FlagLevel.ERROR,
                            field=sensor,
                            message="Core sensor value is null",
                        )
                    )
                    continue
                low, high = self.config.physical_ranges[sensor]
                if not low <= value <= high:
                    flags.append(
                        QualityFlag(
                            code="physical_range",
                            level=FlagLevel.ERROR,
                            field=sensor,
                            message="Outside configured physical limits",
                            observed=value,
                            expected=f"{low} <= value <= {high}",
                        )
                    )
                if prior and getattr(prior, sensor) is not None:
                    elapsed = (row.timestamp - prior.timestamp).total_seconds()
                    if elapsed > 0:
                        change = (
                            abs(value - getattr(prior, sensor))
                            * self.config.expected_interval_seconds
                            / elapsed
                        )
                        threshold = self.config.max_change_per_interval[sensor]
                        if change > threshold:
                            flags.append(
                                QualityFlag(
                                    code="abrupt_change",
                                    level=FlagLevel.WARNING,
                                    field=sensor,
                                    message="Normalized change exceeds limit",
                                    observed=change,
                                    expected=f"<= {threshold}",
                                )
                            )
                rk = (row.station_id, sensor)
                old = repeated.get(rk)
                count = (
                    old[1] + 1
                    if old and abs(value - old[0]) <= self.config.freeze_tolerance
                    else 1
                )
                repeated[rk] = (value, count)
                if count >= self.config.freeze_consecutive:
                    flags.append(
                        QualityFlag(
                            code="frozen_value",
                            level=FlagLevel.WARNING,
                            field=sensor,
                            message=f"Repeated for {count} records",
                            observed=value,
                        )
                    )
            status = (
                QualityStatus.INVALID
                if any(f.level == FlagLevel.ERROR for f in flags)
                else (QualityStatus.SUSPECT if flags else QualityStatus.VALID)
            )
            out.append(ValidatedRecord(observation=row, status=status, flags=flags))
            previous[row.station_id] = row
        return out
