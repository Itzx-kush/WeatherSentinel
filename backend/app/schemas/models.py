"""Canonical schemas; raw values, quality evidence, and features stay separate."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceType(StrEnum):
    REAL = "real"
    SYNTHETIC = "synthetic"
    FAULT_INJECTED = "fault_injected"
    UNKNOWN = "unknown"


class QualityStatus(StrEnum):
    VALID = "valid"
    SUSPECT = "suspect"
    INVALID = "invalid"


class FlagLevel(StrEnum):
    WARNING = "warning"
    ERROR = "error"


class StationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    station_id: str = Field(min_length=1, max_length=128)
    name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    elevation_m: float | None = None
    expected_interval_seconds: int = Field(default=600, gt=0)
    timezone_name: str = "UTC"

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class AWSObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    station_id: str = Field(min_length=1, max_length=128)
    timestamp: datetime
    temperature_c: float | None
    pressure_hpa: float | None
    relative_humidity_pct: float | None

    @field_validator("timestamp")
    @classmethod
    def aware_timestamp(cls, v):
        if v.tzinfo is None:
            raise ValueError("timestamp must include timezone information")
        return v.astimezone(UTC)

    @field_validator("temperature_c", "pressure_hpa", "relative_humidity_pct")
    @classmethod
    def finite(cls, v):
        if v is not None and not math.isfinite(v):
            raise ValueError("sensor values must be finite")
        return v


class DatasetProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: str = Field(min_length=1, max_length=128)
    source_filename: str
    source_type: SourceType
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    record_count: int = Field(ge=0)
    schema_version: str = "aws-observation-v1"
    processing_version: str = "part1-0.1.0"
    random_seed: int | None = None
    notes: str | None = None


class QualityFlag(BaseModel):
    code: str
    level: FlagLevel
    field: str | None = None
    message: str
    observed: float | str | None = None
    expected: str | None = None


class ValidatedRecord(BaseModel):
    observation: AWSObservation
    status: QualityStatus
    flags: list[QualityFlag] = Field(default_factory=list)


class FeatureRecord(BaseModel):
    observation: AWSObservation
    quality_status: QualityStatus
    quality_flags: list[QualityFlag]
    temporal_features: dict[str, dict[str, float | int | None]]
    multivariate_features: dict[str, float | None]
    normal_baseline: dict[str, float | None]


class IngestionError(BaseModel):
    row_number: int
    code: str
    message: str
    raw_record: dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    observations: list[AWSObservation]
    errors: list[IngestionError]
    provenance: DatasetProvenance
