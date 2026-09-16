from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.models import AWSObservation, StationMetadata

class ProcessRequest(BaseModel):
    observations: list[AWSObservation] = Field(min_length=1)
    dataset_id: str = "api-runtime"

class DatasetRequest(ProcessRequest):
    pass

class StationRegistrationRequest(BaseModel):
    stations: list[StationMetadata] = Field(min_length=1)

class FaultInjectionRequest(BaseModel):
    fault_type: str
    sensor: str
    start: int
    end: int
    magnitude: float = 10.0
    station_id: str | None = None

class CorrectionActionRequest(BaseModel):
    minimum_confidence: float = 0.65

class ApiError(BaseModel):
    error: str
    detail: str
    request_id: str

class StatusResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: datetime
