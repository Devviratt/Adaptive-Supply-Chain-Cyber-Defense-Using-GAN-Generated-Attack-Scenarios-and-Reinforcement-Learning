"""
ASCCD CTGAN Trainer — synthetic attack scenario model training.

Trains a Conditional Tabular GAN (CTGAN) strictly on preprocessed training data
to learn continuous and discrete distributions of network attack patterns.
Designed for reproducibility, leak-free training, and artifact persistence.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from ctgan import CTGAN

from src.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CTGANTrainingReport:
    """Detailed record of CTGAN training metadata and parameters."""

    epochs: int = 300
    batch_size: int = 500
    generator_dim: list[int] = field(default_factory=lambda: [256, 256])
    discriminator_dim: list[int] = field(default_factory=lambda: [256, 256])
    generator_lr: float = 2.0e-4
    discriminator_lr: float = 2.0e-4
    discriminator_steps: int = 1
    seed: int = 42
    training_duration_seconds: float = 0.0
    num_samples_trained: int = 0
    num_features: int = 0
    discrete_columns: list[str] = field(default_factory=list)
    feature_names: list[str] = field(default_factory=list)
    classes_present: list[str] = field(default_factory=list)
    class_distribution: dict[str, int] = field(default_factory=dict)
    model_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)

    def save(self, filepath: str | Path) -> None:
        """Save report to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info("ctgan_training_report_saved", filepath=str(path))


class CTGANTrainer:
    """Trainer for Conditional Tabular GAN on processed cybersecurity features.

    Strict Leakage Prevention:
      - Accepts only training partition (`data/processed/train.csv`).
      - Never fits or samples using validation or test datasets.
      - Preserves discrete label mappings and input column order.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
        seed: int = 42,
        **kwargs: Any,
    ) -> None:
        self.config = self._load_config(config, config_path)
        self.seed = seed or self.config.get("seed", 42)

        # Extract hyperparameters with defaults
        ctgan_cfg = self.config.get("ctgan", self.config)
        self.epochs: int = kwargs.get("epochs", ctgan_cfg.get("epochs", 300))
        self.batch_size: int = kwargs.get("batch_size", ctgan_cfg.get("batch_size", 500))
        self.generator_dim: list[int] = kwargs.get(
            "generator_dim", ctgan_cfg.get("generator_dim", [256, 256])
        )
        self.discriminator_dim: list[int] = kwargs.get(
            "discriminator_dim", ctgan_cfg.get("discriminator_dim", [256, 256])
        )
        self.generator_lr: float = kwargs.get("generator_lr", ctgan_cfg.get("generator_lr", 2.0e-4))
        self.discriminator_lr: float = kwargs.get(
            "discriminator_lr", ctgan_cfg.get("discriminator_lr", 2.0e-4)
        )
        self.discriminator_steps: int = kwargs.get(
            "discriminator_steps", ctgan_cfg.get("discriminator_steps", 1)
        )
        self.verbose: bool = kwargs.get("verbose", ctgan_cfg.get("verbose", False))
        self.pac: int = kwargs.get("pac", 10)

        # Batch size validation for CTGAN pac compatibility
        if self.batch_size % 2 != 0:
            self.batch_size = (self.batch_size // 2) * 2
            logger.warning("adjusted_batch_size_to_even", new_batch_size=self.batch_size)

        if self.batch_size % self.pac != 0:
            # Adjust pac to a divisor of batch_size or adjust pac to 1
            for candidate in [10, 8, 4, 2, 1]:
                if self.batch_size % candidate == 0:
                    self.pac = candidate
                    break

        self.model: CTGAN | None = None
        self.report: CTGANTrainingReport | None = None
        self._feature_names: list[str] = []
        self._discrete_columns: list[str] = []

    def _load_config(
        self, config: dict[str, Any] | None, config_path: str | Path | None
    ) -> dict[str, Any]:
        """Load configuration dictionary or read from YAML."""
        if config is not None:
            return config

        path = config_path or Path("config/gan.yaml")
        if Path(path).exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}

        logger.warning("gan_config_not_found_using_defaults", path=str(path))
        return {}

    def fit(
        self,
        train_data: pd.DataFrame,
        discrete_columns: list[str] | None = None,
    ) -> CTGANTrainer:
        """Fit CTGAN model on the provided training dataframe.

        Args:
            train_data: Clean, preprocessed training DataFrame (must not contain NaN/Inf).
            discrete_columns: Names of categorical/discrete columns (default: ['Label']).

        Returns:
            self (fitted trainer).
        """
        if not isinstance(train_data, pd.DataFrame):
            raise TypeError(f"train_data must be pd.DataFrame, got {type(train_data)}")

        if train_data.empty:
            raise ValueError("train_data cannot be empty")

        # Check for non-finite values
        if train_data.isnull().any().any():
            raise ValueError("train_data contains NaN values; clean data before CTGAN training")

        numeric_cols = train_data.select_dtypes(include=[np.number]).columns
        if not np.isfinite(train_data[numeric_cols].values).all():
            raise ValueError(
                "train_data contains Infinite values; clean data before CTGAN training"
            )

        self._feature_names = list(train_data.columns)

        # Detect discrete columns
        if discrete_columns is not None:
            self._discrete_columns = list(discrete_columns)
        elif "Label" in train_data.columns:
            self._discrete_columns = ["Label"]
        else:
            self._discrete_columns = list(
                train_data.select_dtypes(include=["object", "category"]).columns
            )

        # Verify all discrete columns exist in train_data
        missing_disc = set(self._discrete_columns) - set(train_data.columns)
        if missing_disc:
            raise ValueError(f"Discrete columns not found in train_data: {missing_disc}")

        # Class distribution audit
        classes_present: list[str] = []
        class_dist: dict[str, int] = {}
        if "Label" in train_data.columns:
            class_counts = train_data["Label"].value_counts().to_dict()
            classes_present = sorted(str(c) for c in class_counts)
            class_dist = {str(k): int(v) for k, v in class_counts.items()}

        logger.info(
            "starting_ctgan_training",
            rows=len(train_data),
            features=len(self._feature_names),
            discrete_columns=self._discrete_columns,
            epochs=self.epochs,
            batch_size=self.batch_size,
            seed=self.seed,
        )

        # Adjust batch size if training data is smaller than configured batch_size
        effective_batch_size = self.batch_size
        effective_pac = self.pac
        if len(train_data) < effective_batch_size:
            effective_batch_size = max(2, (len(train_data) // 2) * 2)
            for candidate in [10, 8, 4, 2, 1]:
                if effective_batch_size % candidate == 0:
                    effective_pac = candidate
                    break
            logger.info(
                "adjusted_batch_size_for_small_dataset",
                effective_batch_size=effective_batch_size,
                effective_pac=effective_pac,
            )

        start_time = time.time()

        # Initialize CTGAN synthesizer
        self.model = CTGAN(
            embedding_dim=128,
            generator_dim=tuple(self.generator_dim),
            discriminator_dim=tuple(self.discriminator_dim),
            generator_lr=self.generator_lr,
            discriminator_lr=self.discriminator_lr,
            batch_size=effective_batch_size,
            discriminator_steps=self.discriminator_steps,
            verbose=self.verbose,
            epochs=self.epochs,
            pac=effective_pac,
        )
        self.model.set_random_state(self.seed)

        # Train on train_data
        self.model.fit(train_data, discrete_columns=self._discrete_columns)
        duration = time.time() - start_time

        self.report = CTGANTrainingReport(
            epochs=self.epochs,
            batch_size=effective_batch_size,
            generator_dim=self.generator_dim,
            discriminator_dim=self.discriminator_dim,
            generator_lr=self.generator_lr,
            discriminator_lr=self.discriminator_lr,
            discriminator_steps=self.discriminator_steps,
            seed=self.seed,
            training_duration_seconds=round(duration, 3),
            num_samples_trained=len(train_data),
            num_features=len(self._feature_names),
            discrete_columns=self._discrete_columns,
            feature_names=self._feature_names,
            classes_present=classes_present,
            class_distribution=class_dist,
        )

        logger.info(
            "ctgan_training_completed",
            duration_seconds=round(duration, 3),
            epochs=self.epochs,
            num_samples=len(train_data),
        )

        return self

    def save(self, model_path: str | Path, report_path: str | Path | None = None) -> None:
        """Persist fitted CTGAN model and its training report.

        Args:
            model_path: Filepath where model will be saved (e.g. artifacts/models/ctgan.pkl).
            report_path: Optional JSON path for metadata report. If None, saves as <model_path>.json.
        """
        if self.model is None:
            raise RuntimeError("Cannot save untrained CTGAN model. Call fit() first.")

        model_file = Path(model_path)
        model_file.parent.mkdir(parents=True, exist_ok=True)

        self.model.save(str(model_file))
        logger.info("ctgan_model_saved", path=str(model_file))

        rep_path = Path(report_path) if report_path else model_file.with_suffix(".json")
        if self.report:
            self.report.save(rep_path)

    @classmethod
    def load(
        cls,
        model_path: str | Path,
        report_path: str | Path | None = None,
    ) -> CTGANTrainer:
        """Load trained CTGAN model and associated metadata.

        Args:
            model_path: Path to serialized model file.
            report_path: Path to metadata JSON. If None, searches <model_path>.json.

        Returns:
            Initialized CTGANTrainer ready for sampling.
        """
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        trainer = cls()
        trainer.model = CTGAN.load(str(model_file))

        meta_file = Path(report_path) if report_path else model_file.with_suffix(".json")
        if not meta_file.exists() and (model_file.parent / "training_metadata.json").exists():
            meta_file = model_file.parent / "training_metadata.json"

        if meta_file.exists():
            with open(meta_file) as f:
                data = json.load(f)
                trainer.report = CTGANTrainingReport(**data)
                trainer._feature_names = data.get("feature_names", [])
                trainer._discrete_columns = data.get("discrete_columns", [])
                trainer.seed = data.get("seed", 42)

        logger.info("ctgan_model_loaded", path=str(model_file))
        return trainer
