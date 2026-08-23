from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, create_database
from app.db_models import StatusMessageRecord
from app.models import GpsPayload, StatusMessage, StatusMessageCreate


STATUS_MESSAGE_TTL = timedelta(hours=2)
MAX_ACTIVE_STATUS_MESSAGES = 2


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class StatusMessageStore:
    def __init__(
        self,
        database_url: str | None = None,
        now_provider=utc_now,
    ) -> None:
        self.engine, self._session_factory = create_database(database_url)
        Base.metadata.create_all(self.engine)
        self._now_provider = now_provider

    def create(
        self,
        node_id: str,
        payload: StatusMessageCreate,
        latest_gps: GpsPayload | None = None,
    ) -> StatusMessage:
        now = as_utc(self._now_provider())
        with self._session_factory() as session:
            self._expire_messages(session, node_id, now)
            active_records = session.scalars(
                select(StatusMessageRecord).where(
                    StatusMessageRecord.node_id == node_id,
                    StatusMessageRecord.ended_at.is_(None),
                ).order_by(StatusMessageRecord.created_at.asc())
            ).all()
            if len(active_records) >= MAX_ACTIVE_STATUS_MESSAGES:
                oldest = active_records[0]
                oldest.ended_at = now
                oldest.end_reason = "replaced"

            record = StatusMessageRecord(
                id=str(uuid4()),
                node_id=node_id,
                pid=payload.pid,
                category=payload.category,
                message=payload.message,
                lat=latest_gps.lat if latest_gps else None,
                lon=latest_gps.lon if latest_gps else None,
                created_at=now,
                expires_at=now + STATUS_MESSAGE_TTL,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_model(record, now)

    def active_for_node(self, node_id: str) -> StatusMessage | None:
        messages = self.active_messages_for_node(node_id)
        return messages[0] if messages else None

    def active_messages_for_node(self, node_id: str) -> list[StatusMessage]:
        now = as_utc(self._now_provider())
        with self._session_factory() as session:
            self._expire_messages(session, node_id, now)
            records = session.scalars(
                select(StatusMessageRecord).where(
                    StatusMessageRecord.node_id == node_id,
                    StatusMessageRecord.ended_at.is_(None),
                    StatusMessageRecord.expires_at > now,
                ).order_by(StatusMessageRecord.created_at.desc())
            ).all()
            session.commit()
            return [self._to_model(record, now) for record in records]

    def active_for_nodes(self, node_ids: list[str]) -> dict[str, list[StatusMessage]]:
        if not node_ids:
            return {}

        now = as_utc(self._now_provider())
        with self._session_factory() as session:
            self._expire_messages(session, now=now)
            records = session.scalars(
                select(StatusMessageRecord).where(
                    StatusMessageRecord.node_id.in_(node_ids),
                    StatusMessageRecord.ended_at.is_(None),
                    StatusMessageRecord.expires_at > now,
                ).order_by(
                    StatusMessageRecord.node_id.asc(),
                    StatusMessageRecord.created_at.desc(),
                )
            ).all()
            session.commit()
            messages_by_node: dict[str, list[StatusMessage]] = {node_id: [] for node_id in node_ids}
            for record in records:
                messages_by_node.setdefault(record.node_id, []).append(self._to_model(record, now))
            return messages_by_node

    def history(self, node_id: str, limit: int = 20) -> list[StatusMessage]:
        now = as_utc(self._now_provider())
        with self._session_factory() as session:
            self._expire_messages(session, node_id, now)
            records = session.scalars(
                select(StatusMessageRecord)
                .where(StatusMessageRecord.node_id == node_id)
                .order_by(StatusMessageRecord.created_at.desc())
                .limit(limit)
            ).all()
            session.commit()
            return [self._to_model(record, now) for record in records]

    def clear(self, node_id: str, pid: str) -> bool:
        now = as_utc(self._now_provider())
        with self._session_factory() as session:
            self._expire_messages(session, node_id, now)
            record = session.scalar(
                select(StatusMessageRecord).where(
                    StatusMessageRecord.node_id == node_id,
                    StatusMessageRecord.pid == pid,
                    StatusMessageRecord.ended_at.is_(None),
                    StatusMessageRecord.expires_at > now,
                ).order_by(StatusMessageRecord.created_at.desc())
            )
            if record is None:
                session.commit()
                return False
            record.ended_at = now
            record.end_reason = "cleared"
            session.commit()
            return True

    def _expire_messages(
        self,
        session: Session,
        node_id: str | None = None,
        now: datetime | None = None,
    ) -> None:
        effective_now = now or as_utc(self._now_provider())
        query = select(StatusMessageRecord).where(
            StatusMessageRecord.ended_at.is_(None),
            StatusMessageRecord.expires_at <= effective_now,
        )
        if node_id is not None:
            query = query.where(StatusMessageRecord.node_id == node_id)
        expired_records = session.scalars(query).all()
        for record in expired_records:
            record.ended_at = effective_now
            record.end_reason = "expired"

    @staticmethod
    def _to_model(record: StatusMessageRecord, now: datetime) -> StatusMessage:
        if record.ended_at is None and as_utc(record.expires_at) > now:
            state = "active"
        elif record.end_reason == "cleared":
            state = "cleared"
        elif record.end_reason == "replaced":
            state = "replaced"
        else:
            state = "expired"

        return StatusMessage(
            id=record.id,
            node_id=record.node_id,
            pid=record.pid,
            category=record.category,
            message=record.message,
            lat=record.lat,
            lon=record.lon,
            created_at=as_utc(record.created_at),
            expires_at=as_utc(record.expires_at),
            ended_at=as_utc(record.ended_at) if record.ended_at else None,
            end_reason=record.end_reason,
            state=state,
        )
