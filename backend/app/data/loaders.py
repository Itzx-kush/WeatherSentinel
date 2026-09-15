"""Bounded CSV/Parquet ingestion preserving malformed rows as structured errors."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas.models import (
    AWSObservation,
    DatasetProvenance,
    IngestionError,
    IngestionResult,
    SourceType,
)

REQUIRED_COLUMNS = {
    "station_id",
    "timestamp",
    "temperature_c",
    "pressure_hpa",
    "relative_humidity_pct",
}


class DataIngestor:
    def __init__(self, max_file_bytes: int = 50 * 1024 * 1024):
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        self.max_file_bytes = max_file_bytes

    def _path(self, path, suffixes):
        p = Path(path).resolve()
        if not p.is_file():
            raise FileNotFoundError(p)
        if p.suffix.lower() not in suffixes:
            raise ValueError(f"unsupported file extension: {p.suffix}")
        if p.stat().st_size > self.max_file_bytes:
            raise ValueError("file exceeds configured size limit")
        return p

    @staticmethod
    def _number(value: Any) -> float | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        try:
            if value != value:
                return None
        except TypeError:
            pass
        return float(value)

    def from_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        dataset_id: str,
        source_filename: str,
        source_type: SourceType,
        random_seed: int | None = None,
    ) -> IngestionResult:
        accepted = []
        errors = []
        total = 0
        for total, record in enumerate(records, start=1):
            raw = dict(record)
            missing = REQUIRED_COLUMNS - raw.keys()
            if missing:
                errors.append(
                    IngestionError(
                        row_number=total,
                        code="missing_columns",
                        message=f"missing: {sorted(missing)}",
                        raw_record=raw,
                    )
                )
                continue
            try:
                accepted.append(
                    AWSObservation(
                        station_id=str(raw["station_id"]).strip(),
                        timestamp=raw["timestamp"],
                        temperature_c=self._number(raw["temperature_c"]),
                        pressure_hpa=self._number(raw["pressure_hpa"]),
                        relative_humidity_pct=self._number(raw["relative_humidity_pct"]),
                    )
                )
            except (ValidationError, ValueError, TypeError) as exc:
                errors.append(
                    IngestionError(
                        row_number=total, code="malformed_record", message=str(exc), raw_record=raw
                    )
                )
        provenance = DatasetProvenance(
            dataset_id=dataset_id,
            source_filename=source_filename,
            source_type=source_type,
            record_count=total,
            random_seed=random_seed,
        )
        return IngestionResult(observations=accepted, errors=errors, provenance=provenance)

    def from_csv(self, path, *, dataset_id, source_type=SourceType.UNKNOWN):
        p = self._path(path, {".csv"})
        with p.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
            return self.from_records(
                reader, dataset_id=dataset_id, source_filename=p.name, source_type=source_type
            )

    def from_parquet(self, path, *, dataset_id, source_type=SourceType.UNKNOWN):
        p = self._path(path, {".parquet", ".pq"})
        import pandas as pd

        frame = pd.read_parquet(p)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"Parquet is missing required columns: {sorted(missing)}")
        return self.from_records(
            frame.to_dict(orient="records"),
            dataset_id=dataset_id,
            source_filename=p.name,
            source_type=source_type,
        )
