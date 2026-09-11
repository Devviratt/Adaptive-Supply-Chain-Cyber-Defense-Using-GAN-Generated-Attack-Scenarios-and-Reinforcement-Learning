"""
ASCCD Custom Exceptions.

Centralized exception definitions for clean error handling across modules.
"""

from __future__ import annotations


class ASCCDError(Exception):
    """Base exception for all ASCCD errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ASCCDError):
    """Raised when configuration is invalid or missing."""

    pass


class DatasetError(ASCCDError):
    """Raised for dataset loading/processing errors."""

    pass


class DatasetNotFoundError(DatasetError):
    """Raised when a required dataset file is missing."""

    pass


class PreprocessingError(ASCCDError):
    """Raised during data preprocessing failures."""

    pass


class GANError(ASCCDError):
    """Raised for GAN training/generation errors."""

    pass


class GANNotTrainedError(GANError):
    """Raised when GAN model has not been trained yet."""

    pass


class ScenarioMappingError(ASCCDError):
    """Raised for scenario mapping failures."""

    pass


class EnvironmentError(ASCCDError):
    """Raised for supply-chain environment errors."""

    pass


class RLError(ASCCDError):
    """Raised for reinforcement learning errors."""

    pass


class ModelNotTrainedError(RLError):
    """Raised when RL model has not been trained yet."""

    pass


class EvaluationError(ASCCDError):
    """Raised for evaluation engine errors."""

    pass


class ExperimentError(ASCCDError):
    """Raised for experiment execution errors."""

    pass


class AuthenticationError(ASCCDError):
    """Raised for authentication/authorization failures."""

    pass
