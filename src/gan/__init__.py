"""ASCCD GAN module — CTGAN model training, conditional attack generation, and statistical validation."""

from src.gan.evaluation import DownstreamUtilityEvaluator, DownstreamUtilityReport
from src.gan.generator import GenerationMetadata, SyntheticAttackGenerator
from src.gan.trainer import CTGANTrainer, CTGANTrainingReport
from src.gan.validator import SyntheticDataValidator, ValidationSummary, ValidationThresholds

__all__ = [
    "CTGANTrainer",
    "CTGANTrainingReport",
    "SyntheticAttackGenerator",
    "GenerationMetadata",
    "SyntheticDataValidator",
    "ValidationSummary",
    "ValidationThresholds",
    "DownstreamUtilityEvaluator",
    "DownstreamUtilityReport",
]
