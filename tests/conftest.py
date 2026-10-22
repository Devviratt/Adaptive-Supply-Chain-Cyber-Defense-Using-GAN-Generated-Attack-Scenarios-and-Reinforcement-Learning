"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_ENV"] = "testing"
os.environ["APP_DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT


@pytest.fixture
def db_engine():
    """Create a fresh in-memory database engine for each test."""
    import src.common.models  # noqa: F401 — register models
    from src.common.database import Base, create_db_engine

    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing."""
    from sqlalchemy.orm import sessionmaker

    session_class = sessionmaker(bind=db_engine)
    session = session_class()
    yield session
    session.close()


@pytest.fixture
def api_client(db_session):
    """Create a FastAPI test client with database dependency override."""
    from fastapi.testclient import TestClient
    from src.api.deps import get_db
    from src.api.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
