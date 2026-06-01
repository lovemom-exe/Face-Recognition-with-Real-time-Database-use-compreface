from __future__ import annotations

from contextlib import contextmanager
import logging
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "students_mvp" not in table_names:
        return

    statements = []
    students_columns = {column["name"] for column in inspector.get_columns("students_mvp")}
    if "cohort" not in students_columns:
        statements.append("ALTER TABLE students_mvp ADD COLUMN cohort VARCHAR(50)")
    if "major" not in students_columns:
        statements.append("ALTER TABLE students_mvp ADD COLUMN major VARCHAR(150)")

    if "attendance_logs_mvp" in table_names:
        log_columns = {column["name"] for column in inspector.get_columns("attendance_logs_mvp")}
        if "method" not in log_columns:
            statements.append("ALTER TABLE attendance_logs_mvp ADD COLUMN method VARCHAR(30) NOT NULL DEFAULT 'FACE'")
            statements.append("UPDATE attendance_logs_mvp SET method = 'MANUAL' WHERE status = 'MANUAL'")
            statements.append("UPDATE attendance_logs_mvp SET method = 'AUTO_ABSENT' WHERE status = 'ABSENT'")

    if not statements:
        return

    try:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
    except Exception as exc:  # pragma: no cover - defensive compatibility path
        logger.warning("SQLite compatibility update skipped: %s", exc)
