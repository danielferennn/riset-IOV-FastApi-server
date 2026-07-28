from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PidAssignment(BaseModel):
    node_id: str
    pids: list[str]


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3)


class RegisterResponse(BaseModel):
    email: str
    node_id: str
    device_type: Literal["raspi", "phone"]
    pids: list[str]


class GpsPayload(BaseModel):
    node_id: str = Field(min_length=1)
    pid: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)
    speed_mps: float | None = Field(default=None, ge=0)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    altitude_m: float | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    node_id: str = Field(min_length=1)
    pid: str = Field(min_length=1)
    battery: float | None = Field(default=None, ge=0, le=100)
    fuel_level_pct: float | None = Field(default=None, ge=0, le=100)
    speed_kph: float | None = Field(default=None, ge=0)
    odometer_km: float | None = Field(default=None, ge=0)
    temperature_c: float | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NodeEvent(BaseModel):
    event_type: Literal["gps", "telemetry"]
    node_id: str
    pid: str
    timestamp: datetime
    payload: dict[str, Any]


class NodeSnapshot(BaseModel):
    node_id: str
    pids: list[str]
    latest_gps: GpsPayload | None = None
    latest_telemetry: TelemetryPayload | None = None


class ErrorResponse(BaseModel):
    detail: str
