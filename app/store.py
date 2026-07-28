from collections import deque
import json
from pathlib import Path
from threading import Lock
from typing import Any

from app.models import GpsPayload, NodeEvent, NodeSnapshot, TelemetryPayload
from app.pid_registry import PID_ASSIGNMENTS


class TelemetryStore:
    def __init__(self, max_events: int = 500, data_dir: str | Path = "data") -> None:
        self._data_dir = Path(data_dir)
        self._events_path = self._data_dir / "events.jsonl"
        self._latest_path = self._data_dir / "latest_nodes.json"
        self._lock = Lock()
        self._latest_gps: dict[str, GpsPayload] = {}
        self._latest_telemetry: dict[str, TelemetryPayload] = {}
        self._events: deque[NodeEvent] = deque(maxlen=max_events)
        self._load_from_disk()

    def add_gps(self, payload: GpsPayload) -> NodeEvent:
        self._latest_gps[payload.node_id] = payload
        event = NodeEvent(
            event_type="gps",
            node_id=payload.node_id,
            pid=payload.pid,
            timestamp=payload.timestamp,
            payload=payload.model_dump(mode="json"),
        )
        self._events.append(event)
        self._persist_event(event)
        self._persist_latest()
        return event

    def add_telemetry(self, payload: TelemetryPayload) -> NodeEvent:
        self._latest_telemetry[payload.node_id] = payload
        event = NodeEvent(
            event_type="telemetry",
            node_id=payload.node_id,
            pid=payload.pid,
            timestamp=payload.timestamp,
            payload=payload.model_dump(mode="json"),
        )
        self._events.append(event)
        self._persist_event(event)
        self._persist_latest()
        return event

    def snapshots(self) -> list[NodeSnapshot]:
        node_ids = set(PID_ASSIGNMENTS) | set(self._latest_gps) | set(self._latest_telemetry)
        return [self.snapshot(node_id) for node_id in sorted(node_ids)]

    def snapshot(self, node_id: str) -> NodeSnapshot:
        return NodeSnapshot(
            node_id=node_id,
            pids=PID_ASSIGNMENTS.get(node_id, []),
            latest_gps=self._latest_gps.get(node_id),
            latest_telemetry=self._latest_telemetry.get(node_id),
        )

    def events(self, limit: int) -> list[NodeEvent]:
        if len(self._events) == 0:
            return []
        limit = max(1, min(limit, len(self._events)))
        return list(self._events)[-limit:]

    def clear(self, delete_files: bool = False) -> None:
        self._latest_gps.clear()
        self._latest_telemetry.clear()
        self._events.clear()
        if delete_files:
            self._events_path.unlink(missing_ok=True)
            self._latest_path.unlink(missing_ok=True)

    def _persist_event(self, event: NodeEvent) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.model_dump(mode="json"), separators=(",", ":"))
        with self._lock:
            with self._events_path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")

    def _persist_latest(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        snapshots = {
            snapshot.node_id: snapshot.model_dump(mode="json")
            for snapshot in self.snapshots()
        }
        content = json.dumps(snapshots, indent=2)
        with self._lock:
            self._latest_path.write_text(content + "\n", encoding="utf-8")

    def _load_from_disk(self) -> None:
        self._load_latest()
        self._load_recent_events()

    def _load_latest(self) -> None:
        if not self._latest_path.exists():
            return

        try:
            raw_snapshots = json.loads(self._latest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        for raw_snapshot in raw_snapshots.values():
            latest_gps = raw_snapshot.get("latest_gps")
            latest_telemetry = raw_snapshot.get("latest_telemetry")
            if latest_gps:
                gps_payload = GpsPayload.model_validate(latest_gps)
                self._latest_gps[gps_payload.node_id] = gps_payload
            if latest_telemetry:
                telemetry_payload = TelemetryPayload.model_validate(latest_telemetry)
                self._latest_telemetry[telemetry_payload.node_id] = telemetry_payload

    def _load_recent_events(self) -> None:
        if not self._events_path.exists():
            return

        try:
            lines = self._events_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return

        for line in lines[-self._events.maxlen :]:
            if not line.strip():
                continue
            try:
                self._events.append(NodeEvent.model_validate_json(line))
            except ValueError:
                continue


class WebSocketHub:
    def __init__(self) -> None:
        self._clients: set[Any] = set()

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: Any) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, event: NodeEvent) -> None:
        stale_clients = []
        for client in self._clients:
            try:
                await client.send_json(event.model_dump(mode="json"))
            except RuntimeError:
                stale_clients.append(client)

        for client in stale_clients:
            self.disconnect(client)
