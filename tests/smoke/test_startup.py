"""
Smoke tests — verify the core application starts and responds.
"""


class TestApplicationStartup:
    """Verify the application can start and serve requests."""

    def test_app_creates_successfully(self):
        """FastAPI app should be importable and constructable."""
        from src.api.main import app

        assert app is not None
        assert app.title == "ASCCD — Adaptive Supply Chain Cyber Defense"

    def test_health_endpoint_responds(self, api_client):
        """Health endpoint should respond after app starts."""
        response = api_client.get("/api/health")
        assert response.status_code == 200

    def test_config_loads(self):
        """Configuration system should load without errors."""
        from src.common.config import get_settings

        settings = get_settings()
        assert settings.app_name == "ASCCD"

    def test_database_initializes(self):
        """Database should initialize without errors."""
        import src.common.models  # noqa: F401
        from src.common.database import create_db_engine, init_db

        engine = create_db_engine("sqlite:///:memory:")
        init_db(engine)

        # Verify tables exist
        from sqlalchemy import inspect

        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "scenarios" in table_names
        assert "experiments" in table_names
        assert "experiment_metrics" in table_names
        assert "simulation_runs" in table_names
        assert "training_runs" in table_names
        assert "system_events" in table_names

        engine.dispose()

    def test_logger_creates(self):
        """Structured logger should be creatable."""
        from src.common.logging import get_logger

        logger = get_logger("test")
        assert logger is not None
