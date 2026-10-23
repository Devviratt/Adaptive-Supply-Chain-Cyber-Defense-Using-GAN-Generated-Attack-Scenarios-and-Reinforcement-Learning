"""
ASCCD Data Splitter — reproducible train/validation/test splitting.

Implements stratified splitting with configurable ratios and
metadata tracking for the CIC-IDS2017 preprocessing pipeline.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from src.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SplitStatistics:
    """Statistics about a train/val/test split."""

    train_size: int = 0
    val_size: int = 0
    test_size: int = 0
    total_size: int = 0
    train_ratio_actual: float = 0.0
    val_ratio_actual: float = 0.0
    test_ratio_actual: float = 0.0
    train_class_distribution: dict[str, int] = field(default_factory=dict)
    val_class_distribution: dict[str, int] = field(default_factory=dict)
    test_class_distribution: dict[str, int] = field(default_factory=dict)
    stratified: bool = True
    random_seed: int = 42
    label_column: str = "Label"

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_size": self.train_size,
            "val_size": self.val_size,
            "test_size": self.test_size,
            "total_size": self.total_size,
            "train_ratio_actual": round(self.train_ratio_actual, 4),
            "val_ratio_actual": round(self.val_ratio_actual, 4),
            "test_ratio_actual": round(self.test_ratio_actual, 4),
            "train_class_distribution": self.train_class_distribution,
            "val_class_distribution": self.val_class_distribution,
            "test_class_distribution": self.test_class_distribution,
            "stratified": self.stratified,
            "random_seed": self.random_seed,
            "label_column": self.label_column,
        }

    def save(self, filepath: str | Path) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info("split_statistics_saved", filepath=str(filepath))


def stratified_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    label_column: str = "Label",
    random_seed: int = 42,
    stratify: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SplitStatistics]:
    """Split a DataFrame into train, validation, and test sets.

    Performs a two-stage split:
      1. Split into train and (val+test)
      2. Split (val+test) into val and test

    This ensures proper stratification at each stage.

    Args:
        df: Input DataFrame with features and label column.
        train_ratio: Fraction for training (default 0.70).
        val_ratio: Fraction for validation (default 0.15).
        test_ratio: Fraction for test (default 0.15).
        label_column: Name of the label column.
        random_seed: Seed for reproducibility.
        stratify: Whether to stratify by label column.

    Returns:
        Tuple of (train_df, val_df, test_df, statistics).

    Raises:
        ValueError: If ratios don't sum to ~1.0 or data is too small.
    """
    # Validate ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise ValueError(
            f"Split ratios must sum to 1.0, got {total_ratio:.4f} "
            f"(train={train_ratio}, val={val_ratio}, test={test_ratio})"
        )

    if len(df) < 10:
        raise ValueError(f"Dataset too small for splitting: {len(df)} rows")

    # Ensure label column exists for stratification
    stratify_col = None
    if stratify:
        if label_column not in df.columns:
            logger.warning(
                "stratify_column_missing",
                column=label_column,
                message="Falling back to non-stratified split",
            )
            stratify = False
        else:
            # Check minimum samples per class for stratification
            class_counts = df[label_column].value_counts()
            min_count = class_counts.min()
            if min_count < 3:
                # Need at least 3 samples to split into 3 sets
                rare_classes = class_counts[class_counts < 3].index.tolist()
                logger.warning(
                    "rare_classes_detected",
                    classes=rare_classes,
                    min_count=min_count,
                    message="Removing rare classes for stratification",
                )
                df = df[~df[label_column].isin(rare_classes)].reset_index(drop=True)
            stratify_col = df[label_column]

    # Stage 1: Split into train and (val+test)
    val_test_ratio = val_ratio + test_ratio
    train_df, val_test_df = train_test_split(
        df,
        test_size=val_test_ratio,
        random_state=random_seed,
        stratify=stratify_col,
    )

    # Stage 2: Split (val+test) into val and test
    # test fraction relative to val_test combined
    relative_test_ratio = test_ratio / val_test_ratio

    stratify_val_test = None
    if stratify and label_column in val_test_df.columns:
        stratify_val_test = val_test_df[label_column]

    val_df, test_df = train_test_split(
        val_test_df,
        test_size=relative_test_ratio,
        random_state=random_seed,
        stratify=stratify_val_test,
    )

    # Reset indices
    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # Compute statistics
    total = len(train_df) + len(val_df) + len(test_df)
    stats = SplitStatistics(
        train_size=len(train_df),
        val_size=len(val_df),
        test_size=len(test_df),
        total_size=total,
        train_ratio_actual=len(train_df) / total,
        val_ratio_actual=len(val_df) / total,
        test_ratio_actual=len(test_df) / total,
        stratified=stratify,
        random_seed=random_seed,
        label_column=label_column,
    )

    if label_column in df.columns:
        stats.train_class_distribution = train_df[label_column].value_counts().to_dict()
        stats.val_class_distribution = val_df[label_column].value_counts().to_dict()
        stats.test_class_distribution = test_df[label_column].value_counts().to_dict()

    logger.info(
        "data_split_complete",
        train=len(train_df),
        val=len(val_df),
        test=len(test_df),
        stratified=stratify,
        seed=random_seed,
    )

    return train_df, val_df, test_df, stats
