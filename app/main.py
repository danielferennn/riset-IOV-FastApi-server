import os

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
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
    TelemetryPayload,
)
from app.pid_registry import get_pids_for_node, is_valid_pid, list_assignments, register_node
from app.store import TelemetryStore, WebSocketHub


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


@app.get("/nodes", response_model=list[NodeSnapshot])
async def get_nodes() -> list[NodeSnapshot]:
    return store.snapshots()


@app.get("/broadcast/latest", response_model=list[NodeSnapshot])
async def get_broadcast_latest() -> list[NodeSnapshot]:
    return store.snapshots()


@app.get("/nodes/{node_id}/latest", response_model=NodeSnapshot)
async def get_latest_node_data(node_id: str) -> NodeSnapshot:
    if get_pids_for_node(node_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node tidak ditemukan")
    return store.snapshot(node_id)


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
