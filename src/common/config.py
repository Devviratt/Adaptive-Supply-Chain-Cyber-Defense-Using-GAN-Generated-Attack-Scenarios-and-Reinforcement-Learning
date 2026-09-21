"""
ASCCD Configuration Loader.

Loads settings from YAML config files and environment variables.
Configuration hierarchy: defaults → YAML file → environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings

# Project root is two levels up from src/common/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class AppSettings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    # Application
    app_name: str = "ASCCD"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'asccd.db'}"

    # Authentication
    secret_key: str = "CHANGE-THIS-TO-A-RANDOM-SECRET-KEY"
    access_token_expire_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "CHANGE-THIS-PASSWORD"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Data paths
    data_raw_dir: str = str(PROJECT_ROOT / "data" / "raw")
    data_processed_dir: str = str(PROJECT_ROOT / "data" / "processed")
    data_generated_dir: str = str(PROJECT_ROOT / "data" / "generated")

    # ML
    device: str = "cpu"
    random_seed: int = 42

    # MLflow
    mlflow_tracking_uri: str = f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}"
    mlflow_experiment_name: str = "asccd-experiments"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


def load_yaml_config(config_name: str) -> dict[str, Any]:
    """Load a YAML configuration file from the config/ directory.

    Args:
        config_name: Name of the config file (with or without .yaml extension).

    Returns:
        Dictionary of configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if isinstance(config_name, Path):
        config_path = config_name
    else:
        name_str = str(config_name)
        if not (name_str.endswith(".yaml") or name_str.endswith(".yml")):
            name_str = f"{name_str}.yaml"
        target_path = Path(name_str)
        config_path = target_path if target_path.is_absolute() else CONFIG_DIR / target_path

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    return config


def load_config(config_name: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load configuration with optional overrides.

    Merges YAML config with any runtime overrides.

    Args:
        config_name: Name of the YAML config file.
        overrides: Optional dict of values to override.

    Returns:
        Merged configuration dictionary.
    """
    config = load_yaml_config(config_name)

    if overrides:
        config = _deep_merge(config, overrides)

    return config


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Get cached application settings singleton."""
    return AppSettings()
