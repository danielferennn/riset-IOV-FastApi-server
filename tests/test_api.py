import asyncio

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import app.main as api
from app.models import GpsPayload, RegisterRequest, TelemetryPayload
from app.store import TelemetryStore


RASPI_PID = "pid_3f9a0c8e12d44bb7a98f21cd"
PHONE_01_PID = "pid_64b79ea172304899be1170aa"
RASPI_02_PID = "pid_b2d80ad7910c4a45bbd5688e"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api, "store", TelemetryStore(data_dir=tmp_path))


def test_health() -> None:
    response = asyncio.run(api.health())

    assert response == {"status": "ok"}


def test_map_page_contains_broadcast_polling() -> None:
    response = asyncio.run(api.map_page())

    assert "IOV Node Map" in response
    assert 'fetch("broadcast/latest"' in response
    assert 'phone: "static/markers/pedestrian.png"' in response
    assert "popup-metrics" in response
    assert "Baterai" in response


def test_root_path_is_empty_by_default(monkeypatch) -> None:
    monkeypatch.delenv("IOV_ROOT_PATH", raising=False)

    assert api.get_root_path() == ""


def test_root_path_normalizes_reverse_proxy_prefix(monkeypatch) -> None:
    monkeypatch.setenv("IOV_ROOT_PATH", "/riset-iov/")

    assert api.get_root_path() == "/riset-iov"


def test_get_node_pids() -> None:
    response = asyncio.run(api.get_node_pids("raspi-01"))

    assert response.node_id == "raspi-01"
    assert len(response.pids) == 5
    assert response.pids[0].startswith("pid_")


def test_register_node_by_email_returns_hardcoded_pid_pool() -> None:
    response = asyncio.run(
        api.register_node_by_email(RegisterRequest(email="Raspi@Example.com"))
    )

    assert response.email == "raspi@example.com"
    assert response.node_id == "raspi-01"
    assert response.device_type == "raspi"
    assert len(response.pids) == 5
    assert response.pids[0] == RASPI_PID


def test_register_second_raspi_node() -> None:
    response = asyncio.run(
        api.register_node_by_email(RegisterRequest(email="raspi2@example.com"))
    )

    assert response.node_id == "raspi-02"
    assert response.device_type == "raspi"
    assert len(response.pids) == 5
    assert response.pids[0] == RASPI_02_PID


def test_register_unknown_email_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            api.register_node_by_email(RegisterRequest(email="unknown@example.com"))
        )

    assert exc_info.value.status_code == 404


def test_rejects_pid_from_other_node() -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            api.ingest_gps(
                GpsPayload(
                    node_id="phone-01",
                    pid=RASPI_PID,
                    lat=-6.2,
                    lon=106.8,
                )
            )
        )

    assert exc_info.value.status_code == 403


def test_ingest_gps_updates_latest_snapshot() -> None:
    response = asyncio.run(
        api.ingest_gps(
            GpsPayload(
                node_id="phone-01",
                pid=PHONE_01_PID,
                lat=-6.2,
                lon=106.8,
                speed_mps=4.5,
            )
        )
    )

    assert response.event_type == "gps"
    latest = api.store.snapshot("phone-01")
    assert latest.latest_gps is not None
    assert latest.latest_gps.lat == -6.2
    assert latest.latest_gps.lon == 106.8
    assert latest.latest_telemetry is None


def test_ingest_telemetry_updates_latest_snapshot_and_events() -> None:
    response = asyncio.run(
        api.ingest_telemetry(
            TelemetryPayload(
                node_id="raspi-01",
                pid=RASPI_PID,
                battery=78.5,
                fuel_level_pct=63,
                speed_kph=42,
                odometer_km=12034.5,
                temperature_c=87,
                extra={"obd_protocol": "ISO 15765-4 CAN"},
            )
        )
    )

    assert response.event_type == "telemetry"
    latest = api.store.snapshot("raspi-01")
    assert latest.latest_telemetry is not None
    assert latest.latest_telemetry.battery == 78.5
    assert latest.latest_telemetry.odometer_km == 12034.5

    events = api.store.events(limit=100)
    assert len(events) == 1
    assert events[0].event_type == "telemetry"


def test_broadcast_latest_returns_all_node_snapshots() -> None:
    asyncio.run(
        api.ingest_gps(
            GpsPayload(
                node_id="phone-01",
                pid=PHONE_01_PID,
                lat=-6.2,
                lon=106.8,
            )
        )
    )

    snapshots = asyncio.run(api.get_broadcast_latest())
    snapshot_by_node_id = {snapshot.node_id: snapshot for snapshot in snapshots}

    assert len(snapshots) == 5
    assert set(snapshot_by_node_id) == {"raspi-01", "raspi-02", "raspi-03", "phone-01", "phone-02"}
    assert snapshot_by_node_id["phone-01"].latest_gps is not None


def test_jsonl_storage_persists_events_and_latest_snapshot(tmp_path) -> None:
    store = TelemetryStore(data_dir=tmp_path)

    store.add_gps(
        GpsPayload(
            node_id="phone-01",
            pid=PHONE_01_PID,
            lat=-6.2,
            lon=106.8,
        )
    )
    store.add_telemetry(
        TelemetryPayload(
            node_id="raspi-01",
            pid=RASPI_PID,
            battery=78.5,
            fuel_level_pct=63,
            speed_kph=42,
            odometer_km=12034.5,
            temperature_c=87,
        )
    )

    restored_store = TelemetryStore(data_dir=tmp_path)
    events = restored_store.events(limit=10)
    raspi_latest = restored_store.snapshot("raspi-01").latest_telemetry

    assert len(events) == 2
    assert events[-1].event_type == "telemetry"
    assert raspi_latest is not None
    assert raspi_latest.model_dump()["battery"] == 78.5
    assert raspi_latest.odometer_km == 12034.5


def test_rejects_battery_outside_percentage_range() -> None:
    with pytest.raises(ValidationError):
        TelemetryPayload(
            node_id="raspi-01",
            pid=RASPI_PID,
            battery=100.1,
        )
