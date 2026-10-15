"""
ASCCD Synthetic Attack Generator — conditional and unconditional attack synthesis.

Generates realistic, schema-compliant synthetic network attack feature vectors
conditioned on specific cyber attack categories. Enforces strict schema conformity,
physical constraints (e.g., non-negative packet counts), and class availability.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from ctgan import CTGAN

from src.common.logging import get_logger
from src.gan.trainer import CTGANTrainer

logger = get_logger(__name__)


@dataclass
class GenerationMetadata:
    """Metadata tracking generated synthetic attack batches."""

    total_samples: int = 0
    class_distribution: dict[str, int] = field(default_factory=dict)
    generation_mode: str = "unconditional"  # "unconditional" or "conditional"
    requested_class_counts: dict[str, int] = field(default_factory=dict)
    shortfall_classes: dict[str, int] = field(default_factory=dict)
    nan_rows_filtered: int = 0
    inf_rows_filtered: int = 0
    clamped_features_count: int = 0
    feature_count: int = 0
    column_names: list[str] = field(default_factory=list)
    seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)

    def save(self, filepath: str | Path) -> None:
        """Save metadata to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class SyntheticAttackGenerator:
    """Conditional synthetic data generator built on trained CTGAN models."""

    def __init__(
        self,
        trainer: CTGANTrainer | None = None,
        model: CTGAN | None = None,
        feature_names: list[str] | None = None,
        valid_labels: list[str] | None = None,
        seed: int = 42,
    ) -> None:
        if trainer is not None:
            self.model: CTGAN = trainer.model
            self.feature_names: list[str] = list(trainer._feature_names)
            self.valid_labels: list[str] = (
                list(trainer.report.classes_present) if trainer.report else []
            )
            self.seed: int = trainer.seed
        elif model is not None:
            self.model = model
            self.feature_names = list(feature_names or [])
            self.valid_labels = list(valid_labels or [])
            self.seed = seed
        else:
            raise ValueError("Either 'trainer' or 'model' must be provided.")

        if self.model is None:
            raise ValueError("Provided model/trainer is not trained or initialized.")

        self.last_metadata: GenerationMetadata | None = None

    @classmethod
    def from_checkpoint(
        cls,
        model_path: str | Path,
        metadata_path: str | Path | None = None,
    ) -> SyntheticAttackGenerator:
        """Instantiate generator directly from saved model checkpoint."""
        trainer = CTGANTrainer.load(model_path, metadata_path)
        return cls(trainer=trainer)

    def generate(
        self,
        num_samples: int,
        seed: int | None = None,
        enforce_schema: bool = True,
    ) -> pd.DataFrame:
        """Generate unconditional synthetic samples from the learned distribution.

        Args:
            num_samples: Number of synthetic instances to sample.
            seed: Optional random seed for reproducible sampling.
            enforce_schema: Whether to align columns and clean non-finite values.

        Returns:
            pd.DataFrame of generated synthetic samples.
        """
        if num_samples <= 0:
            raise ValueError(f"num_samples must be positive integer, got {num_samples}")

        if seed is not None:
            self.model.set_random_state(seed)

        logger.info("generating_unconditional_synthetic_data", num_samples=num_samples)
        raw_df = self.model.sample(num_samples)

        if enforce_schema:
            cleaned_df, meta = self._postprocess_and_clean(
                raw_df, mode="unconditional", seed=seed or self.seed
            )
            self.last_metadata = meta
            return cleaned_df

        return raw_df

    def generate_conditional(
        self,
        class_counts: dict[str, int],
        max_resample_attempts: int = 8,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """Generate targeted quantities of synthetic attack classes.

        Strict Safety Rules:
          - Validates that requested classes exist in training distribution.
          - Rejects requests for classes not seen during training.
          - Uses conditional sampling with rejection resampling for minority classes.

        Args:
            class_counts: Mapping from class label (e.g., 'dos', 'ddos') to desired count.
            max_resample_attempts: Maximum retries when sampling rare classes.
            seed: Optional random seed.

        Returns:
            pd.DataFrame containing balanced synthetic attack samples.
        """
        if not class_counts:
            raise ValueError("class_counts cannot be empty")

        if seed is not None:
            self.model.set_random_state(seed)

        # Validate that requested classes exist in training labels
        if self.valid_labels:
            invalid_classes = set(class_counts.keys()) - set(self.valid_labels)
            if invalid_classes:
                raise ValueError(
                    f"Requested classes {invalid_classes} were not present in training data. "
                    f"Available classes: {self.valid_labels}. "
                    "Cannot fabricate data for absent classes."
                )

        logger.info(
            "generating_conditional_synthetic_data",
            target_classes=class_counts,
        )

        accumulated_dfs: list[pd.DataFrame] = []
        shortfall_classes: dict[str, int] = {}

        for label_name, target_count in class_counts.items():
            if target_count <= 0:
                continue

            collected_samples: list[pd.DataFrame] = []
            current_count = 0
            attempts = 0

            # Attempt conditioned sampling
            while current_count < target_count and attempts < max_resample_attempts:
                attempts += 1
                needed = target_count - current_count
                # Over-sample to account for conditioning probability
                sample_batch_size = max(10, needed * 2)

                try:
                    batch = self.model.sample(
                        sample_batch_size,
                        condition_column="Label",
                        condition_value=label_name,
                    )
                except Exception as exc:
                    logger.warning(
                        "conditional_sampling_failed_falling_back_to_unconditional",
                        label=label_name,
                        error=str(exc),
                    )
                    batch = self.model.sample(sample_batch_size)

                # Filter only matching class
                if "Label" in batch.columns:
                    matching = batch[batch["Label"] == label_name]
                    if not matching.empty:
                        collected_samples.append(matching)
                        current_count += len(matching)

            if collected_samples:
                combined_class = pd.concat(collected_samples, ignore_index=True)
                if len(combined_class) > target_count:
                    combined_class = combined_class.iloc[:target_count]
                accumulated_dfs.append(combined_class)
            else:
                combined_class = pd.DataFrame()

            if current_count < target_count:
                shortfall = target_count - current_count
                shortfall_classes[label_name] = shortfall
                logger.warning(
                    "conditional_generation_shortfall_for_rare_class",
                    class_name=label_name,
                    requested=target_count,
                    generated=current_count,
                    shortfall=shortfall,
                )

        if not accumulated_dfs:
            raise RuntimeError("Failed to generate any valid samples for requested classes.")

        raw_df = pd.concat(accumulated_dfs, ignore_index=True)
        cleaned_df, meta = self._postprocess_and_clean(
            raw_df,
            mode="conditional",
            seed=seed or self.seed,
            requested_counts=class_counts,
            shortfalls=shortfall_classes,
        )
        self.last_metadata = meta
        return cleaned_df

    def _postprocess_and_clean(
        self,
        df: pd.DataFrame,
        mode: str,
        seed: int,
        requested_counts: dict[str, int] | None = None,
        shortfalls: dict[str, int] | None = None,
    ) -> tuple[pd.DataFrame, GenerationMetadata]:
        """Align columns to training schema, clamp physical limits, and clean non-finites."""
        cleaned = df.copy()

        # Align column order if feature_names is known
        if self.feature_names:
            present_cols = [c for c in self.feature_names if c in cleaned.columns]
            cleaned = cleaned[present_cols]

        nan_before = int(cleaned.isnull().sum().sum())
        numeric_cols = cleaned.select_dtypes(include=[np.number]).columns

        # Check infinite values
        inf_mask = np.isinf(cleaned[numeric_cols].values)
        inf_before = int(np.sum(inf_mask))

        # Clean NaN / Inf by dropping or clipping
        if nan_before > 0 or inf_before > 0:
            cleaned.replace([np.inf, -np.inf], np.nan, inplace=True)
            cleaned.dropna(inplace=True)

        # Non-negative clamping for physical network quantities
        clamped_features = 0
        non_negative_keywords = [
            "Duration",
            "Packets",
            "Bytes",
            "Length",
            "IAT",
            "Header",
            "Size",
            "Rate",
        ]
        for col in numeric_cols:
            if any(kw in col for kw in non_negative_keywords):
                negatives = (cleaned[col] < 0).sum()
                if negatives > 0:
                    cleaned[col] = cleaned[col].clip(lower=0.0)
                    clamped_features += 1

        # Class distribution count
        class_dist: dict[str, int] = {}
        if "Label" in cleaned.columns:
            counts = cleaned["Label"].value_counts().to_dict()
            class_dist = {str(k): int(v) for k, v in counts.items()}

        metadata = GenerationMetadata(
            total_samples=len(cleaned),
            class_distribution=class_dist,
            generation_mode=mode,
            requested_class_counts=requested_counts or {},
            shortfall_classes=shortfalls or {},
            nan_rows_filtered=nan_before,
            inf_rows_filtered=inf_before,
            clamped_features_count=clamped_features,
            feature_count=len(cleaned.columns),
            column_names=list(cleaned.columns),
            seed=seed,
        )

        logger.info(
            "synthetic_postprocessing_complete",
            final_rows=len(cleaned),
            clamped_features=clamped_features,
            classes=class_dist,
        )

        return cleaned, metadata

    def save_synthetic_data(
        self,
        df: pd.DataFrame,
        output_csv_path: str | Path,
        metadata_path: str | Path | None = None,
    ) -> None:
        """Save synthetic DataFrame and corresponding metadata."""
        out_csv = Path(output_csv_path)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False)
        logger.info("synthetic_data_saved_csv", path=str(out_csv), rows=len(df))

        meta_out = Path(metadata_path) if metadata_path else out_csv.with_suffix(".metadata.json")
        if self.last_metadata:
            self.last_metadata.save(meta_out)
        else:
            meta = GenerationMetadata(
                total_samples=len(df),
                feature_count=len(df.columns),
                column_names=list(df.columns),
                class_distribution=(
                    df["Label"].value_counts().to_dict() if "Label" in df.columns else {}
                ),
            )
            meta.save(meta_out)
