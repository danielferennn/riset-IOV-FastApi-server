import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return os.getenv("IOV_DATABASE_URL", "sqlite:///data/iov.db")


def create_database(database_url: str | None = None) -> tuple[object, sessionmaker[Session]]:
    url = database_url or get_database_url()
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative_path = url.removeprefix("sqlite:///")
        Path(relative_path).parent.mkdir(parents=True, exist_ok=True)

    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
