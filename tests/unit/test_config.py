"""
Unit tests for the configuration system.
"""

import pytest


class TestAppSettings:
    """Tests for Pydantic AppSettings."""

    def test_default_settings_load(self):
        """Settings should load with defaults even without .env file."""
        from src.common.config import AppSettings

        settings = AppSettings()
        assert settings.app_name == "ASCCD"
        assert settings.app_port == 8000
        assert settings.random_seed == 42
        assert settings.device == "cpu"

    def test_cors_origins_parsing(self):
        """CORS origins string should parse to list."""
        from src.common.config import AppSettings

        settings = AppSettings()
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) >= 1

    def test_database_url_default(self):
        """Default database URL should be SQLite."""
        from src.common.config import AppSettings

        settings = AppSettings()
        assert "sqlite" in settings.database_url


class TestYamlConfig:
    """Tests for YAML configuration loading."""

    def test_load_base_config(self):
        """Should load base.yaml successfully."""
        from src.common.config import load_yaml_config

        config = load_yaml_config("base")
        assert "project" in config
        assert config["project"]["name"] == "ASCCD"

    def test_load_dqn_config(self):
        """Should load dqn.yaml with reward configuration."""
        from src.common.config import load_yaml_config

        config = load_yaml_config("dqn")
        assert "dqn" in config
        assert "reward" in config
        assert "weights" in config["reward"]

    def test_load_nonexistent_config_raises(self):
        """Should raise FileNotFoundError for missing config."""
        from src.common.config import load_yaml_config

        with pytest.raises(FileNotFoundError):
            load_yaml_config("nonexistent_config")

    def test_deep_merge(self):
        """Deep merge should recursively merge dicts."""
        from src.common.config import _deep_merge

        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}, "e": 5}
        result = _deep_merge(base, override)

        assert result["a"]["b"] == 10
        assert result["a"]["c"] == 2
        assert result["d"] == 3
        assert result["e"] == 5

    def test_load_config_with_overrides(self):
        """Should merge YAML config with overrides."""
        from src.common.config import load_config

        config = load_config("base", overrides={"project": {"version": "99.0.0"}})
        assert config["project"]["version"] == "99.0.0"
        assert config["project"]["name"] == "ASCCD"  # Original preserved
