from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


StatusMessageCategory = Literal[
    "traffic",
    "road_condition",
    "hazard",
    "weather",
    "info",
]

StatusMessageState = Literal["active", "expired", "cleared", "replaced"]

ReportCategory = Literal[
    "road_damage",
    "traffic",
    "accident",
    "flood",
    "obstacle",
    "other",
]


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


class StatusMessageCreate(BaseModel):
    pid: str = Field(min_length=1)
    category: StatusMessageCategory
    message: str = Field(min_length=1, max_length=280)


class StatusMessage(BaseModel):
    id: str
    node_id: str
    pid: str
    category: StatusMessageCategory
    message: str
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    created_at: datetime
    expires_at: datetime
    ended_at: datetime | None = None
    end_reason: Literal["expired", "cleared", "replaced"] | None = None
    state: StatusMessageState


class ReportPhoto(BaseModel):
    id: str
    url: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class Report(BaseModel):
    id: str
    node_id: str
    pid: str
    category: ReportCategory
    title: str
    description: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    created_at: datetime
    photos: list[ReportPhoto] = Field(default_factory=list)


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
    active_message: StatusMessage | None = None
    active_messages: list[StatusMessage] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
