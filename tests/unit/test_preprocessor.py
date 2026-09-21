"""
Unit tests for ASCCD Data Preprocessor (src/data/preprocessor.py).

Tests cleaning, missing/inf handling, label normalization, variance and
correlation feature selection, strict train-only fit (leakage prevention),
and artifact persistence.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data.preprocessor import DataPreprocessor


@pytest.fixture
def sample_config() -> dict:
    """Return a representative preprocessing config dictionary."""
    return {
        "random_seed": 42,
        "drop_columns": ["Flow ID", "Source IP", "Destination Port"],
        "missing_values": {"strategy": "drop_rows", "column_threshold": 0.5},
        "inf_handling": "replace_with_nan",
        "scaler": "standard",
        "feature_selection": {
            "variance_threshold": 0.05,
            "correlation_threshold": 0.90,
        },
        "label_mapping": {
            "BENIGN": "benign",
            "DoS Hulk": "dos",
            "PortScan": "portscan",
            "Web Attack – Brute Force": "web_attack",
            "Web Attack - XSS": "web_attack",
        },
        "valid_labels": ["benign", "dos", "portscan", "web_attack", "unknown"],
    }


@pytest.fixture
def dirty_dataframe() -> pd.DataFrame:
    """Create a DataFrame containing duplicates, NaNs, Infs, and metadata columns."""
    return pd.DataFrame(
        {
            "Flow ID": ["id1", "id2", "id3", "id4", "id5", "id5"],
            "Destination Port": [80, 443, 22, 80, 80, 80],
            "feature_normal": [10.0, 20.0, 30.0, 40.0, 50.0, 50.0],
            "feature_constant": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Zero variance
            "feature_high_corr": [20.0, 40.0, 60.0, 80.0, 100.0, 100.0],  # 1.0 corr with normal
            "feature_inf": [1.0, np.inf, 3.0, 4.0, 5.0, 5.0],
            "feature_nan": [1.0, 2.0, np.nan, 4.0, 5.0, 5.0],
            "Label": [
                "BENIGN",
                "DoS Hulk",
                "PortScan",
                "Web Attack \x96 Brute Force",
                "UnknownAttack",
                "UnknownAttack",
            ],
        }
    )


def test_drop_configured_columns(sample_config: dict, dirty_dataframe: pd.DataFrame):
    """Test dropping metadata/identifier columns specified in config."""
    preprocessor = DataPreprocessor(sample_config)
    df = preprocessor.drop_configured_columns(dirty_dataframe)

    assert "Flow ID" not in df.columns
    assert "Destination Port" not in df.columns
    assert "feature_normal" in df.columns


def test_clean_inf_nan_and_duplicates(sample_config: dict, dirty_dataframe: pd.DataFrame):
    """Test cleaning handles duplicates, replaces Infs, and drops or imputes NaNs."""
    preprocessor = DataPreprocessor(sample_config)
    cleaned = preprocessor.clean(dirty_dataframe)

    # Duplicates should be removed
    assert len(cleaned) < len(dirty_dataframe)
    # Inf should be converted and dropped/handled
    for col in cleaned.select_dtypes(include=[np.number]).columns:
        assert not np.isinf(cleaned[col]).any()
        assert not cleaned[col].isna().any()


def test_normalize_labels_mapping_and_quirks(sample_config: dict):
    """Test label normalization including unknown fallbacks and en-dash quirks."""
    df = pd.DataFrame(
        {
            "feat": [1, 2, 3, 4],
            "Label": [
                "BENIGN",
                "DoS Hulk",
                "Web Attack \x96 Brute Force",  # Windows-1252 byte quirk
                "UnseenLabel",
            ],
        }
    )
    preprocessor = DataPreprocessor(sample_config)
    normalized = preprocessor.normalize_labels(df)

    expected = ["benign", "dos", "web_attack", "unknown"]
    assert list(normalized["Label"]) == expected


def test_feature_selection_variance_and_correlation(sample_config: dict):
    """Test that zero/low variance and highly correlated features are eliminated."""
    rng = np.random.default_rng(42)
    x1 = rng.normal(0, 1, 100)
    x2 = x1 * 2.0 + rng.normal(0, 0.001, 100)  # Near 1.0 correlation
    x3 = np.zeros(100)  # Zero variance
    x4 = rng.normal(5, 2, 100)  # Independent feature

    X = pd.DataFrame({"normal": x1, "collinear": x2, "zero_var": x3, "indep": x4})
    preprocessor = DataPreprocessor(sample_config)
    X_selected, rep = preprocessor.select_features(X)

    assert "zero_var" not in X_selected.columns
    assert not ("normal" in X_selected.columns and "collinear" in X_selected.columns)
    assert "indep" in X_selected.columns
    assert rep["final_count"] < rep["original_count"]


def test_leakage_prevention(sample_config: dict):
    """Verify that scaler parameters are derived EXCLUSIVELY from training data."""
    train_df = pd.DataFrame(
        {
            "val1": [10.0, 20.0, 30.0],
            "val2": [100.0, 200.0, 300.0],
            "Label": ["benign", "dos", "benign"],
        }
    )
    # Val set has extreme values that would distort the scaler mean if leaked
    val_df = pd.DataFrame(
        {
            "val1": [1000.0, 2000.0],
            "val2": [10000.0, 20000.0],
            "Label": ["benign", "dos"],
        }
    )
    test_df = pd.DataFrame(
        {
            "val1": [50.0],
            "val2": [500.0],
            "Label": ["benign"],
        }
    )

    preprocessor = DataPreprocessor(sample_config)
    train_p, val_p, test_p = preprocessor.fit_transform_splits(
        train_df, val_df, test_df, label_column="Label"
    )

    # Expected train mean for val1 is mean([10, 20, 30]) = 20.0
    # Scaler mean must match train mean exactly
    scaler_feature_idx = preprocessor._feature_names.index("val1")
    assert np.isclose(preprocessor.scaler.mean_[scaler_feature_idx], 20.0)

    # val_p should be scaled using the train statistics, NOT val statistics
    # Standardized: (1000 - 20) / std(train) >> 0
    assert val_p["val1"].iloc[0] > 10.0


def test_save_and_load_artifacts(tmp_path: Path, sample_config: dict):
    """Test saving artifacts to disk and restoring a fully functioning preprocessor."""
    train_df = pd.DataFrame(
        {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [10.0, 20.0, 30.0, 40.0],
            "Label": ["benign", "dos", "benign", "dos"],
        }
    )

    preprocessor = DataPreprocessor(sample_config)
    train_p, _, _ = preprocessor.fit_transform_splits(train_df, train_df.copy(), train_df.copy())

    artifacts = preprocessor.save_artifacts(tmp_path)
    assert Path(artifacts["scaler"]).exists()
    assert Path(artifacts["label_encoder"]).exists()
    assert Path(artifacts["feature_list"]).exists()
    assert Path(artifacts["label_mapping"]).exists()
    assert Path(artifacts["preprocessing_report"]).exists()

    # Reload
    loaded = DataPreprocessor.load_artifacts(tmp_path)
    test_features = pd.DataFrame({"f1": [2.5], "f2": [25.0]})
    trans1 = preprocessor.transform(test_features)
    trans2 = loaded.transform(test_features)

    pd.testing.assert_frame_equal(trans1, trans2)


def test_preprocessing_reproducibility(sample_config: dict):
    """Test that running preprocessing twice with the same seed produces identical results."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "f1": rng.normal(0, 1, 100),
            "f2": rng.normal(10, 2, 100),
            "Label": ["benign"] * 70 + ["dos"] * 30,
        }
    )

    p1 = DataPreprocessor(sample_config)
    train1, val1, test1 = p1.fit_transform_splits(df.copy(), df.copy(), df.copy())

    p2 = DataPreprocessor(sample_config)
    train2, val2, test2 = p2.fit_transform_splits(df.copy(), df.copy(), df.copy())

    pd.testing.assert_frame_equal(train1, train2)
    pd.testing.assert_frame_equal(val1, val2)
    pd.testing.assert_frame_equal(test1, test2)
