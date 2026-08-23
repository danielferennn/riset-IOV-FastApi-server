from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps
from sqlalchemy import delete, select

from app.database import Base, create_database
from app.db_models import ReportPhotoRecord, ReportRecord
from app.models import Report, ReportPhoto, ReportCategory


MAX_REPORT_PHOTOS = 3
MAX_PHOTO_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class PreparedPhoto:
    content: bytes
    mime_type: str
    extension: str


class ReportValidationError(ValueError):
    pass


class ReportNotFoundError(LookupError):
    pass


class ReportStore:
    def __init__(
        self,
        database_url: str | None = None,
        upload_dir: str | Path = "uploads/reports",
        now_provider=utc_now,
    ) -> None:
        self.engine, self._session_factory = create_database(database_url)
        Base.metadata.create_all(self.engine)
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._now_provider = now_provider

    def create(
        self,
        *,
        node_id: str,
        pid: str,
        category: ReportCategory,
        title: str,
        description: str,
        lat: float,
        lon: float,
        photos: list[bytes],
    ) -> Report:
        if len(photos) > MAX_REPORT_PHOTOS:
            raise ReportValidationError(f"maksimal {MAX_REPORT_PHOTOS} foto per report")

        prepared_photos = [self._prepare_photo(content) for content in photos]
        now = as_utc(self._now_provider())
        report_id = str(uuid4())
        report_dir = self._upload_dir / report_id
        written_paths: list[Path] = []

        try:
            report_dir.mkdir(parents=True, exist_ok=False)
            photo_records: list[ReportPhotoRecord] = []
            for prepared in prepared_photos:
                photo_id = str(uuid4())
                storage_key = f"{photo_id}.{prepared.extension}"
                photo_path = report_dir / storage_key
                photo_path.write_bytes(prepared.content)
                written_paths.append(photo_path)
                photo_records.append(
                    ReportPhotoRecord(
                        id=photo_id,
                        report_id=report_id,
                        storage_key=f"{report_id}/{storage_key}",
                        mime_type=prepared.mime_type,
                        size_bytes=len(prepared.content),
                        created_at=now,
                    )
                )

            with self._session_factory() as session:
                record = ReportRecord(
                    id=report_id,
                    node_id=node_id,
                    pid=pid,
                    category=category,
                    title=title,
                    description=description,
                    lat=lat,
                    lon=lon,
                    created_at=now,
                )
                session.add(record)
                session.add_all(photo_records)
                session.commit()
                return self._to_model(record, photo_records)
        except Exception:
            for path in written_paths:
                path.unlink(missing_ok=True)
            report_dir.rmdir() if report_dir.exists() and not any(report_dir.iterdir()) else None
            raise

    def list_reports(
        self,
        *,
        limit: int = 100,
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
    ) -> list[Report]:
        with self._session_factory() as session:
            query = select(ReportRecord).order_by(ReportRecord.created_at.desc()).limit(limit)
            if lat_min is not None:
                query = query.where(ReportRecord.lat >= lat_min)
            if lat_max is not None:
                query = query.where(ReportRecord.lat <= lat_max)
            if lon_min is not None:
                query = query.where(ReportRecord.lon >= lon_min)
            if lon_max is not None:
                query = query.where(ReportRecord.lon <= lon_max)
            records = session.scalars(query).all()
            return [self._to_model(record, self._photos_for(session, record.id)) for record in records]

    def get(self, report_id: str) -> Report:
        with self._session_factory() as session:
            record = session.get(ReportRecord, report_id)
            if record is None:
                raise ReportNotFoundError(report_id)
            return self._to_model(record, self._photos_for(session, report_id))

    def delete(self, report_id: str) -> None:
        with self._session_factory() as session:
            record = session.get(ReportRecord, report_id)
            if record is None:
                raise ReportNotFoundError(report_id)

            photos = self._photos_for(session, report_id)
            photo_paths = [self._safe_storage_path(photo.storage_key) for photo in photos]
            session.execute(delete(ReportPhotoRecord).where(ReportPhotoRecord.report_id == report_id))
            session.delete(record)
            session.commit()

        for photo_path in photo_paths:
            photo_path.unlink(missing_ok=True)

        report_dir = (self._upload_dir / report_id).resolve()
        root = self._upload_dir.resolve()
        if root in report_dir.parents and report_dir.is_dir():
            try:
                report_dir.rmdir()
            except OSError:
                # Keep unrelated files rather than deleting anything unexpected.
                pass

    def get_photo_path(self, report_id: str, photo_id: str) -> tuple[Path, str]:
        with self._session_factory() as session:
            photo = session.scalar(
                select(ReportPhotoRecord).where(
                    ReportPhotoRecord.id == photo_id,
                    ReportPhotoRecord.report_id == report_id,
                )
            )
            if photo is None:
                raise ReportNotFoundError(photo_id)
            return self._safe_storage_path(photo.storage_key), photo.mime_type

    def _safe_storage_path(self, storage_key: str) -> Path:
        path = (self._upload_dir / storage_key).resolve()
        root = self._upload_dir.resolve()
        if root not in path.parents:
            raise ReportNotFoundError(storage_key)
        return path

    def _photos_for(self, session, report_id: str) -> list[ReportPhotoRecord]:
        return session.scalars(
            select(ReportPhotoRecord)
            .where(ReportPhotoRecord.report_id == report_id)
            .order_by(ReportPhotoRecord.created_at.asc())
        ).all()

    @staticmethod
    def _prepare_photo(content: bytes) -> PreparedPhoto:
        if not content:
            raise ReportValidationError("foto tidak boleh kosong")
        if len(content) > MAX_PHOTO_BYTES:
            raise ReportValidationError("ukuran foto maksimal 5 MB")

        try:
            with Image.open(BytesIO(content)) as image:
                image.load()
                image_format = image.format
                if image_format not in ALLOWED_IMAGE_FORMATS:
                    raise ReportValidationError("format foto harus JPEG, PNG, atau WebP")
                normalized = ImageOps.exif_transpose(image)
                output = BytesIO()
                if image_format == "JPEG":
                    normalized.convert("RGB").save(output, format="JPEG", quality=90, optimize=True, exif=b"")
                elif image_format == "PNG":
                    normalized.save(output, format="PNG", optimize=True)
                else:
                    normalized.save(output, format="WEBP", quality=90, exif=b"")
        except ReportValidationError:
            raise
        except Exception as exc:
            raise ReportValidationError("file bukan gambar yang valid") from exc

        mime_type, extension = ALLOWED_IMAGE_FORMATS[image_format]
        normalized_content = output.getvalue()
        if len(normalized_content) > MAX_PHOTO_BYTES:
            raise ReportValidationError("ukuran foto setelah diproses maksimal 5 MB")
        return PreparedPhoto(normalized_content, mime_type, extension)

    @staticmethod
    def _to_model(record: ReportRecord, photos: list[ReportPhotoRecord]) -> Report:
        return Report(
            id=record.id,
            node_id=record.node_id,
            pid=record.pid,
            category=record.category,
            title=record.title,
            description=record.description,
            lat=record.lat,
            lon=record.lon,
            created_at=as_utc(record.created_at),
            photos=[
                ReportPhoto(
                    id=photo.id,
                    url=f"reports/{record.id}/photos/{photo.id}",
                    mime_type=photo.mime_type,
                    size_bytes=photo.size_bytes,
                    created_at=as_utc(photo.created_at),
                )
                for photo in photos
            ],
        )
