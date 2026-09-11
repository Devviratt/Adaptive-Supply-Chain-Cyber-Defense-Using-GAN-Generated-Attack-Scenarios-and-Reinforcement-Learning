"""
Unit tests for ASCCD Data Splitter (src/data/splitter.py).

Tests stratified train/val/test splitting, ratio verification, rare class
handling, reproducibility across identical seeds, and statistics export.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data.splitter import stratified_split


@pytest.fixture
def multi_class_dataset() -> pd.DataFrame:
    """Create a synthetic dataset with imbalanced classes for stratification testing."""
    rng = np.random.default_rng(42)
    n = 1000

    labels = ["benign"] * 800 + ["dos"] * 120 + ["portscan"] * 70 + ["rare_attack"] * 10
    rng.shuffle(labels)

    return pd.DataFrame(
        {
            "feature1": rng.normal(0, 1, n),
            "feature2": rng.normal(10, 5, n),
            "Label": labels,
        }
    )


def test_stratified_split_proportions(multi_class_dataset: pd.DataFrame):
    """Test that train, val, and test splits respect requested proportions."""
    train_df, val_df, test_df, stats = stratified_split(
        multi_class_dataset,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        label_column="Label",
        random_seed=42,
    )

    total = len(multi_class_dataset)
    assert len(train_df) == pytest.approx(int(total * 0.70), abs=10)
    assert len(val_df) == pytest.approx(int(total * 0.15), abs=10)
    assert len(test_df) == pytest.approx(int(total * 0.15), abs=10)
    assert len(train_df) + len(val_df) + len(test_df) == total

    assert stats.train_size == len(train_df)
    assert stats.val_size == len(val_df)
    assert stats.test_size == len(test_df)


def test_stratified_split_preserves_class_distribution(multi_class_dataset: pd.DataFrame):
    """Verify class proportions in train/val/test match original distribution."""
    train_df, val_df, test_df, stats = stratified_split(
        multi_class_dataset,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        label_column="Label",
        random_seed=42,
    )

    # Benign proportion ~80%
    assert (train_df["Label"] == "benign").mean() == pytest.approx(0.80, abs=0.03)
    assert (val_df["Label"] == "benign").mean() == pytest.approx(0.80, abs=0.03)
    assert (test_df["Label"] == "benign").mean() == pytest.approx(0.80, abs=0.03)


def test_stratified_split_reproducibility(multi_class_dataset: pd.DataFrame):
    """Identical seeds must yield identical split outputs."""
    t1, v1, te1, _ = stratified_split(multi_class_dataset, random_seed=123, label_column="Label")
    t2, v2, te2, _ = stratified_split(multi_class_dataset, random_seed=123, label_column="Label")

    pd.testing.assert_frame_equal(t1, t2)
    pd.testing.assert_frame_equal(v1, v2)
    pd.testing.assert_frame_equal(te1, te2)


def test_invalid_split_ratios(multi_class_dataset: pd.DataFrame):
    """Test error raised when ratios do not sum to ~1.0."""
    with pytest.raises(ValueError, match="Split ratios must sum to 1.0"):
        stratified_split(multi_class_dataset, train_ratio=0.5, val_ratio=0.1, test_ratio=0.1)


def test_split_statistics_persistence(tmp_path: Path, multi_class_dataset: pd.DataFrame):
    """Test serialization and file saving of SplitStatistics."""
    _, _, _, stats = stratified_split(multi_class_dataset, label_column="Label")
    save_path = tmp_path / "split_stats.json"
    stats.save(save_path)

    assert save_path.exists()
    d = stats.to_dict()
    assert d["train_size"] > 0
    assert "benign" in d["train_class_distribution"]
