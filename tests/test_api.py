import asyncio
from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from PIL import Image

import app.main as api
from app.models import GpsPayload, RegisterRequest, StatusMessageCreate, TelemetryPayload
from app.store import TelemetryStore
from app.status_store import StatusMessageStore
from app.report_store import ReportStore


RASPI_PID = "pid_3f9a0c8e12d44bb7a98f21cd"
PHONE_01_PID = "pid_64b79ea172304899be1170aa"
RASPI_02_PID = "pid_b2d80ad7910c4a45bbd5688e"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api, "store", TelemetryStore(data_dir=tmp_path))
    monkeypatch.setattr(
        api,
        "status_store",
        StatusMessageStore(database_url=f"sqlite:///{tmp_path / 'status_messages.db'}"),
    )
    monkeypatch.setattr(
        api,
        "report_store",
        ReportStore(
            database_url=f"sqlite:///{tmp_path / 'reports.db'}",
            upload_dir=tmp_path / "uploads" / "reports",
        ),
    )


def test_health() -> None:
    response = asyncio.run(api.health())

    assert response == {"status": "ok"}


def test_map_page_contains_broadcast_polling() -> None:
    response = asyncio.run(api.map_page())

    assert "IOV Node Map" in response
    assert 'fetchJsonWithTimeout("broadcast/latest")' in response
    assert 'phone: "static/markers/pedestrian.png"' in response
    assert "popup-metrics" in response
    assert "Baterai" in response
    assert "active_message" in response
    assert "active_messages" in response
    assert "Status Message" in response
    assert 'fetchJsonWithTimeout("reports?limit=100")' in response
    assert "NODE_POLL_INTERVAL_MS = 10000" in response
    assert "REPORT_POLL_INTERVAL_MS = 30000" in response
    assert "REQUEST_TIMEOUT_MS = 10000" in response
    assert "AbortController" in response
    assert "document.hidden" in response
    assert "setInterval(refreshNodes" not in response
    assert "setInterval(refreshReports" not in response
    assert "report-marker" in response
    assert "Log Report" in response
    assert "report-delete" not in response


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


def test_status_message_is_attached_to_node_snapshot() -> None:
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

    message = asyncio.run(
        api.create_status_message(
            "phone-01",
            StatusMessageCreate(
                pid=PHONE_01_PID,
                category="traffic",
                message="Lalu lintas padat",
            ),
        )
    )

    snapshot = api.status_store.active_for_node("phone-01")
    assert message.state == "active"
    assert message.lat == -6.2
    assert message.lon == 106.8
    assert snapshot is not None
    assert snapshot.id == message.id
    assert asyncio.run(api.get_latest_node_data("phone-01")).active_message is not None


def test_two_status_messages_remain_active_and_third_replaces_oldest() -> None:
    first = asyncio.run(
        api.create_status_message(
            "phone-01",
            StatusMessageCreate(
                pid=PHONE_01_PID,
                category="info",
                message="Update pertama",
            ),
        )
    )
    second = asyncio.run(
        api.create_status_message(
            "phone-01",
            StatusMessageCreate(
                pid=PHONE_01_PID,
                category="hazard",
                message="Ada lubang di jalan",
            ),
        )
    )
    third = asyncio.run(
        api.create_status_message(
            "phone-01",
            StatusMessageCreate(
                pid=PHONE_01_PID,
                category="hazard",
                message="Ada lubang di jalan",
            ),
        )
    )

    history = asyncio.run(api.get_status_message_history("phone-01", limit=20))
    assert third.state == "active"
    assert second.state == "active"
    assert history[0].id == third.id
    assert history[1].id == second.id
    assert history[2].id == first.id
    assert history[2].state == "replaced"

    snapshot = asyncio.run(api.get_latest_node_data("phone-01"))
    assert snapshot.active_message is not None
    assert snapshot.active_message.id == third.id
    assert [message.id for message in snapshot.active_messages] == [third.id, second.id]

    asyncio.run(api.clear_status_message("phone-01", pid=PHONE_01_PID))
    remaining = asyncio.run(api.get_status_message("phone-01"))
    assert remaining is not None
    assert remaining.id == second.id


def test_status_message_expires_after_two_hours(tmp_path) -> None:
    current_time = [datetime(2026, 7, 31, 10, 0, tzinfo=timezone.utc)]
    status_store = StatusMessageStore(
        database_url=f"sqlite:///{tmp_path / 'status_messages.db'}",
        now_provider=lambda: current_time[0],
    )
    payload = StatusMessageCreate(
        pid=PHONE_01_PID,
        category="weather",
        message="Hujan deras",
    )

    created = status_store.create("phone-01", payload)
    assert status_store.active_for_node("phone-01") is not None

    current_time[0] += timedelta(hours=2)
    assert status_store.active_for_node("phone-01") is None
    history = status_store.history("phone-01")
    assert history[0].id == created.id
    assert history[0].state == "expired"
    assert history[0].end_reason == "expired"


def test_two_status_messages_expire_independently(tmp_path) -> None:
    current_time = [datetime(2026, 7, 31, 10, 0, tzinfo=timezone.utc)]
    status_store = StatusMessageStore(
        database_url=f"sqlite:///{tmp_path / 'status_messages.db'}",
        now_provider=lambda: current_time[0],
    )

    first = status_store.create(
        "phone-01",
        StatusMessageCreate(pid=PHONE_01_PID, category="info", message="Pesan pertama"),
    )
    current_time[0] += timedelta(hours=1)
    second = status_store.create(
        "phone-01",
        StatusMessageCreate(pid=PHONE_01_PID, category="traffic", message="Pesan kedua"),
    )

    assert [message.id for message in status_store.active_messages_for_node("phone-01")] == [second.id, first.id]

    current_time[0] += timedelta(hours=1, minutes=1)
    active = status_store.active_messages_for_node("phone-01")
    assert [message.id for message in active] == [second.id]
    assert status_store.history("phone-01")[1].state == "expired"


def test_report_can_be_submitted_without_photo() -> None:
    report = asyncio.run(
        api.create_report(
            node_id="phone-01",
            pid=PHONE_01_PID,
            category="road_damage",
            title="Jalan berlubang",
            description="Ada lubang di sisi kiri jalan.",
            lat=-6.2,
            lon=106.8,
            photos=None,
        )
    )

    assert report.category == "road_damage"
    assert report.photos == []
    assert asyncio.run(api.get_report(report.id)).id == report.id


def test_report_can_be_submitted_with_photo_and_photo_is_served() -> None:
    image = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(image, format="PNG")
    report = api.report_store.create(
        node_id="raspi-01",
        pid=RASPI_PID,
        category="obstacle",
        title="Halangan di jalan",
        description="Ada benda menghalangi lajur kendaraan.",
        lat=-6.21,
        lon=106.81,
        photos=[image.getvalue()],
    )

    assert len(report.photos) == 1
    assert report.photos[0].mime_type == "image/png"
    photo_path, mime_type = api.report_store.get_photo_path(report.id, report.photos[0].id)
    assert photo_path.is_file()
    assert mime_type == "image/png"
    served_photo = asyncio.run(api.get_report_photo(report.id, report.photos[0].id))
    assert served_photo.media_type == "image/png"


def test_report_rejects_pid_from_other_node() -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            api.create_report(
                node_id="raspi-01",
                pid=PHONE_01_PID,
                category="traffic",
                title="Test",
                description="PID tidak sesuai node.",
                lat=-6.2,
                lon=106.8,
                photos=None,
            )
        )

    assert exc_info.value.status_code == 403


def test_report_delete_requires_admin_token_and_removes_photo(monkeypatch) -> None:
    image = BytesIO()
    Image.new("RGB", (2, 2), color="blue").save(image, format="PNG")
    report = api.report_store.create(
        node_id="phone-01",
        pid=PHONE_01_PID,
        category="road_damage",
        title="Report untuk dihapus",
        description="Data pengujian.",
        lat=-6.2,
        lon=106.8,
        photos=[image.getvalue()],
    )
    photo_path, _ = api.report_store.get_photo_path(report.id, report.photos[0].id)
    assert photo_path.is_file()

    monkeypatch.delenv("IOV_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(api.delete_report(report.id, admin_token=None))
    assert exc_info.value.status_code == 503

    monkeypatch.setenv("IOV_ADMIN_TOKEN", "test-admin-token")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(api.delete_report(report.id, admin_token="wrong-token"))
    assert exc_info.value.status_code == 401

    asyncio.run(api.delete_report(report.id, admin_token="test-admin-token"))
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(api.get_report(report.id))
    assert exc_info.value.status_code == 404
    assert not photo_path.exists()


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
