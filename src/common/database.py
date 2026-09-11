"""
ASCCD Database Configuration.

SQLAlchemy engine, session management, and base model.
Uses SQLite for local development; schema is PostgreSQL-compatible.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from src.common.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


def create_db_engine(database_url: str | None = None):
    """Create SQLAlchemy engine.

    Args:
        database_url: Override database URL. Defaults to settings.

    Returns:
        SQLAlchemy Engine instance.
    """
    url = database_url or get_settings().database_url

    connect_args = {}
    kwargs = {}

    if url.startswith("sqlite"):
        # SQLite-specific: enable WAL mode, allow same thread sharing
        connect_args["check_same_thread"] = False
        kwargs["poolclass"] = StaticPool

    engine = create_engine(url, connect_args=connect_args, echo=False, **kwargs)

    # Enable WAL mode and foreign keys for SQLite
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine=None) -> sessionmaker:
    """Create a session factory.

    Args:
        engine: SQLAlchemy engine. Creates default if not provided.

    Returns:
        sessionmaker instance.
    """
    if engine is None:
        engine = create_db_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session.

    Yields:
        SQLAlchemy Session that auto-closes after use.
    """
    session_factory = create_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine=None) -> None:
    """Initialize database — create all tables.

    Args:
        engine: SQLAlchemy engine. Creates default if not provided.
    """
    if engine is None:
        engine = create_db_engine()

    # Import models so they register with Base.metadata
    import src.common.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
