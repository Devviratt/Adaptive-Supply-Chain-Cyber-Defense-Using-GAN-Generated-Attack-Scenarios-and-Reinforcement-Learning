"""
ASCCD API Dependencies.

Shared dependencies for FastAPI endpoints — database sessions, auth, etc.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from src.common.database import create_session_factory

_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory()
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """Dependency: provides a database session per request."""
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
