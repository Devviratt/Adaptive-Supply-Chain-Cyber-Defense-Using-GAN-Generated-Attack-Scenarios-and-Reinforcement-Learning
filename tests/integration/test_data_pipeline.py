"""
Integration test for the full ASCCD Phase 2 Data Pipeline.

Tests the end-to-end flow from raw CSV ingestion through cleaning, label
normalization, stratified splitting, train-only transformation fitting,
artifact export, and automated validation.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data.loader import load_dataset
from src.data.preprocessor import DataPreprocessor
from src.data.splitter import stratified_split
from src.data.validator import validate_processed_data


@pytest.fixture
def raw_dataset_dir(tmp_path: Path) -> Path:
    """Create a temporary directory containing multi-file raw CSV fixtures."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    rng = np.random.default_rng(42)
    n1, n2 = 600, 400

    # Day 1 CSV: Benign and DoS
    df1 = pd.DataFrame(
        {
            " Flow ID": [f"flow_{i}" for i in range(n1)],
            " Destination Port": rng.choice([80, 443, 22], size=n1),
            " Flow Duration": rng.exponential(100, size=n1),
            " Total Fwd Packets": rng.integers(1, 50, size=n1),
            " Flow Bytes/s": rng.normal(500, 50, size=n1),
            " Low Var Feat": np.ones(n1),  # Should be dropped by variance threshold
            " Duplicate Col 1": rng.normal(10, 2, size=n1),
            " Label": ["BENIGN"] * 500 + ["DoS Hulk"] * 100,
        }
    )
    # Inject an Inf and a NaN into Day 1
    df1.loc[10, " Flow Bytes/s"] = np.inf
    df1.loc[20, " Flow Duration"] = np.nan
    df1.to_csv(raw_dir / "Monday-WorkingHours.pcap_ISCX.csv", index=False)

    # Day 2 CSV: PortScan, DDoS, Web Attacks
    df2 = pd.DataFrame(
        {
            " Flow ID": [f"flow_d2_{i}" for i in range(n2)],
            " Destination Port": rng.choice([80, 8080, 21], size=n2),
            " Flow Duration": rng.exponential(150, size=n2),
            " Total Fwd Packets": rng.integers(1, 40, size=n2),
            " Flow Bytes/s": rng.normal(450, 60, size=n2),
            " Low Var Feat": np.ones(n2),
            " Duplicate Col 1": rng.normal(10, 2, size=n2),
            " Label": ["BENIGN"] * 250
            + ["PortScan"] * 80
            + ["DDoS"] * 50
            + ["Web Attack – Brute Force"] * 20,
        }
    )
    df2.to_csv(raw_dir / "Friday-WorkingHours-Morning.pcap_ISCX.csv", index=False)

    return raw_dir


def test_end_to_end_data_pipeline(raw_dataset_dir: Path, tmp_path: Path):
    """Test full pipeline execution, artifact creation, and validation pass."""
    processed_dir = tmp_path / "processed"

    config = {
        "random_seed": 42,
        "drop_columns": ["Flow ID", "Destination Port"],
        "missing_values": {"strategy": "drop_rows", "column_threshold": 0.5},
        "inf_handling": "replace_with_nan",
        "scaler": "standard",
        "feature_selection": {
            "variance_threshold": 0.01,
            "correlation_threshold": 0.95,
        },
        "label_mapping": {
            "BENIGN": "benign",
            "DoS Hulk": "dos",
            "PortScan": "portscan",
            "DDoS": "ddos",
            "Web Attack – Brute Force": "web_attack",
        },
        "valid_labels": ["benign", "dos", "portscan", "ddos", "web_attack", "unknown"],
    }

    # Step 1: Ingest
    raw_df, meta = load_dataset(raw_dataset_dir)
    assert meta["files_loaded"] == 2
    assert len(raw_df) == 1000

    # Step 2: Clean & normalize
    preprocessor = DataPreprocessor(config)
    cleaned_df = preprocessor.prepare_raw(raw_df)
    assert len(cleaned_df) >= 990
    assert "Low Var Feat" in cleaned_df.columns

    # Step 3: Stratified split
    train_df, val_df, test_df, stats = stratified_split(
        cleaned_df,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        label_column="Label",
        random_seed=42,
    )
    assert len(train_df) > len(val_df)
    assert len(val_df) == len(test_df) or abs(len(val_df) - len(test_df)) <= 2

    # Step 4: Fit-transform splits (leakage safe)
    train_p, val_p, test_p = preprocessor.fit_transform_splits(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        label_column="Label",
    )

    # Low Var Feat must have been dropped during fit on train
    assert "Low Var Feat" not in train_p.columns
    assert "Low Var Feat" not in val_p.columns
    assert "Low Var Feat" not in test_p.columns

    # Step 5: Save files and artifacts
    processed_dir.mkdir(parents=True)
    train_p.to_csv(processed_dir / "train.csv", index=False)
    val_p.to_csv(processed_dir / "val.csv", index=False)
    test_p.to_csv(processed_dir / "test.csv", index=False)

    preprocessor.save_artifacts(processed_dir)
    stats.save(processed_dir / "split_statistics.json")

    # Step 6: Validate outputs
    report = validate_processed_data(processed_dir, expected_label_col="Label")
    assert report.is_valid is True
    assert report.failed_checks == 0
    assert report.passed_checks >= 8

    # Step 7: Re-load artifacts and verify consistency
    reloaded_preprocessor = DataPreprocessor.load_artifacts(processed_dir)
    sample_feature = train_df[reloaded_preprocessor._feature_names].iloc[:5]
    scaled_orig = preprocessor.transform(sample_feature)
    scaled_reloaded = reloaded_preprocessor.transform(sample_feature)
    pd.testing.assert_frame_equal(scaled_orig, scaled_reloaded)
