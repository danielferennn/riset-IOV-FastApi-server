import os
import secrets

from fastapi import File, FastAPI, Form, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.map_view import MAP_HTML
from app.models import (
    ErrorResponse,
    GpsPayload,
    NodeEvent,
    NodeSnapshot,
    PidAssignment,
    RegisterRequest,
    RegisterResponse,
    Report,
    StatusMessage,
    StatusMessageCreate,
    TelemetryPayload,
)
from app.pid_registry import get_pids_for_node, is_valid_pid, list_assignments, register_node
from app.store import TelemetryStore, WebSocketHub
from app.status_store import StatusMessageStore
from app.report_store import (
    MAX_PHOTO_BYTES,
    MAX_REPORT_PHOTOS,
    ReportNotFoundError,
    ReportStore,
    ReportValidationError,
)


def get_root_path() -> str:
    """Return an optional reverse-proxy path prefix without a trailing slash."""
    root_path = os.getenv("IOV_ROOT_PATH", "").strip()
    if root_path in {"", "/"}:
        return ""
    if not root_path.startswith("/"):
        raise RuntimeError("IOV_ROOT_PATH harus diawali '/'")
    return root_path.rstrip("/")


app = FastAPI(
    title="IOV Backend Prototype",
    description="Backend prototype untuk menerima GPS dan telemetry OBD dari node IOV.",
    version="0.1.0",
    root_path=get_root_path(),
)

store = TelemetryStore(data_dir=os.getenv("IOV_DATA_DIR", "data"))
status_store = StatusMessageStore(database_url=os.getenv("IOV_DATABASE_URL", "sqlite:///data/iov.db"))
report_store = ReportStore(
    database_url=os.getenv("IOV_DATABASE_URL", "sqlite:///data/iov.db"),
    upload_dir=os.getenv("IOV_UPLOAD_DIR", "uploads/reports"),
)
hub = WebSocketHub()

app.mount("/static", StaticFiles(directory="static"), name="static")


def ensure_valid_pid(node_id: str, pid: str) -> None:
    if get_pids_for_node(node_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"node_id '{node_id}' belum terdaftar",
        )
    if not is_valid_pid(node_id, pid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"pid '{pid}' bukan milik node_id '{node_id}'",
        )


def require_admin_token(admin_token: str | None) -> None:
    configured_token = os.getenv("IOV_ADMIN_TOKEN", "").strip()
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="penghapusan report belum dikonfigurasi",
        )
    if not admin_token or not secrets.compare_digest(admin_token, configured_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin token tidak valid")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/map", response_class=HTMLResponse, include_in_schema=False)
async def map_page() -> str:
    return MAP_HTML


@app.get("/pids", response_model=list[PidAssignment])
async def get_pid_assignments() -> list[PidAssignment]:
    return list_assignments()


@app.post(
    "/nodes/register",
    response_model=RegisterResponse,
    responses={404: {"model": ErrorResponse}},
)
async def register_node_by_email(payload: RegisterRequest) -> RegisterResponse:
    registration = register_node(payload.email)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="email node tidak terdaftar")
    return registration


@app.get(
    "/nodes/{node_id}/pids",
    response_model=PidAssignment,
    responses={404: {"model": ErrorResponse}},
)
async def get_node_pids(node_id: str) -> PidAssignment:
    pids = get_pids_for_node(node_id)
    if pids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node tidak ditemukan")
    return PidAssignment(node_id=node_id, pids=pids)


@app.post(
    "/ingest/gps",
    response_model=NodeEvent,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def ingest_gps(payload: GpsPayload) -> NodeEvent:
    ensure_valid_pid(payload.node_id, payload.pid)
    event = store.add_gps(payload)
    await hub.broadcast(event)
    return event


@app.post(
    "/ingest/telemetry",
    response_model=NodeEvent,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def ingest_telemetry(payload: TelemetryPayload) -> NodeEvent:
    ensure_valid_pid(payload.node_id, payload.pid)
    event = store.add_telemetry(payload)
    await hub.broadcast(event)
    return event


def snapshots_with_status_messages() -> list[NodeSnapshot]:
    snapshots = store.snapshots()
    active_messages = status_store.active_for_nodes([snapshot.node_id for snapshot in snapshots])
    return [
        snapshot.model_copy(
            update={
                "active_message": (active_messages.get(snapshot.node_id) or [None])[0],
                "active_messages": active_messages.get(snapshot.node_id, []),
            }
        )
        for snapshot in snapshots
    ]


@app.post(
    "/nodes/{node_id}/status-message",
    response_model=StatusMessage,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_status_message(node_id: str, payload: StatusMessageCreate) -> StatusMessage:
    ensure_valid_pid(node_id, payload.pid)
    latest_gps = store.snapshot(node_id).latest_gps
    return status_store.create(node_id, payload, latest_gps)


@app.get("/nodes/{node_id}/status-message", response_model=StatusMessage | None)
async def get_status_message(node_id: str) -> StatusMessage | None:
    if get_pids_for_node(node_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node tidak ditemukan")
    return status_store.active_for_node(node_id)


@app.delete(
    "/nodes/{node_id}/status-message",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def clear_status_message(node_id: str, pid: str = Query(..., min_length=1)) -> None:
    ensure_valid_pid(node_id, pid)
    if not status_store.clear(node_id, pid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="message aktif tidak ditemukan")


@app.get("/nodes", response_model=list[NodeSnapshot])
async def get_nodes() -> list[NodeSnapshot]:
    return snapshots_with_status_messages()


@app.get("/broadcast/latest", response_model=list[NodeSnapshot])
async def get_broadcast_latest() -> list[NodeSnapshot]:
    return snapshots_with_status_messages()


@app.get("/nodes/{node_id}/latest", response_model=NodeSnapshot)
async def get_latest_node_data(node_id: str) -> NodeSnapshot:
    if get_pids_for_node(node_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node tidak ditemukan")
    snapshot = store.snapshot(node_id)
    active_messages = status_store.active_messages_for_node(node_id)
    return snapshot.model_copy(
        update={
            "active_message": active_messages[0] if active_messages else None,
            "active_messages": active_messages,
        }
    )


@app.get("/nodes/{node_id}/status-messages", response_model=list[StatusMessage])
async def get_status_message_history(
    node_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[StatusMessage]:
    if get_pids_for_node(node_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node tidak ditemukan")
    return status_store.history(node_id, limit)


@app.post(
    "/reports",
    response_model=Report,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_report(
    node_id: str = Form(..., min_length=1),
    pid: str = Form(..., min_length=1),
    category: str = Form(..., min_length=1),
    title: str = Form(..., min_length=1, max_length=120),
    description: str = Form(..., min_length=1, max_length=2000),
    lat: float = Form(..., ge=-90, le=90),
    lon: float = Form(..., ge=-180, le=180),
    photos: list[UploadFile] | None = File(default=None),
) -> Report:
    ensure_valid_pid(node_id, pid)
    if category not in {"road_damage", "traffic", "accident", "flood", "obstacle", "other"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="kategori report tidak valid")
    if photos is not None and len(photos) > MAX_REPORT_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"maksimal {MAX_REPORT_PHOTOS} foto per report",
        )

    photo_contents: list[bytes] = []
    for photo in photos or []:
        try:
            photo.file.seek(0)
            photo_contents.append(photo.file.read(MAX_PHOTO_BYTES + 1))
        finally:
            photo.file.close()

    try:
        return report_store.create(
            node_id=node_id,
            pid=pid,
            category=category,
            title=title,
            description=description,
            lat=lat,
            lon=lon,
            photos=photo_contents,
        )
    except ReportValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@app.get("/reports", response_model=list[Report])
async def get_reports(
    limit: int = Query(default=100, ge=1, le=100),
    lat_min: float | None = Query(default=None, ge=-90, le=90),
    lat_max: float | None = Query(default=None, ge=-90, le=90),
    lon_min: float | None = Query(default=None, ge=-180, le=180),
    lon_max: float | None = Query(default=None, ge=-180, le=180),
) -> list[Report]:
    if lat_min is not None and lat_max is not None and lat_min > lat_max:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rentang latitude tidak valid")
    if lon_min is not None and lon_max is not None and lon_min > lon_max:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rentang longitude tidak valid")
    return report_store.list_reports(
        limit=limit,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
    )


@app.get("/reports/{report_id}/photos/{photo_id}", response_class=FileResponse)
async def get_report_photo(report_id: str, photo_id: str) -> FileResponse:
    try:
        photo_path, mime_type = report_store.get_photo_path(report_id, photo_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="foto report tidak ditemukan") from exc
    if not photo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file foto tidak ditemukan")
    return FileResponse(photo_path, media_type=mime_type)


@app.get("/reports/{report_id}", response_model=Report)
async def get_report(report_id: str) -> Report:
    try:
        return report_store.get(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report tidak ditemukan") from exc


@app.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def delete_report(
    report_id: str,
    admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    require_admin_token(admin_token)
    try:
        report_store.delete(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report tidak ditemukan") from exc


@app.get("/events", response_model=list[NodeEvent])
async def get_events(limit: int = Query(default=100, ge=1, le=500)) -> list[NodeEvent]:
    return store.events(limit)


@app.websocket("/ws/maps")
async def maps_websocket(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
