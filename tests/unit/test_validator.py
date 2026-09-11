"""
Unit tests for ASCCD Data Validator (src/data/validator.py).

Tests verification of splits, schema consistency, detection of NaNs, Infs,
mismatched features, empty splits, missing artifacts, and report generation.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data.validator import DataValidator, validate_processed_data


@pytest.fixture
def valid_dataset_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with valid splits and mock artifacts."""
    data_dir = tmp_path / "processed"
    data_dir.mkdir()

    train_df = pd.DataFrame(
        {
            "feat_1": [0.1, 0.2, 0.3, 0.4],
            "feat_2": [1.1, 1.2, 1.3, 1.4],
            "feat_3": [-0.5, -0.2, 0.0, 0.5],
            "Label": ["benign", "dos", "benign", "dos"],
        }
    )
    val_df = pd.DataFrame(
        {
            "feat_1": [0.15, 0.25],
            "feat_2": [1.15, 1.25],
            "feat_3": [-0.3, 0.2],
            "Label": ["benign", "dos"],
        }
    )
    test_df = val_df.copy()

    train_df.to_csv(data_dir / "train.csv", index=False)
    val_df.to_csv(data_dir / "val.csv", index=False)
    test_df.to_csv(data_dir / "test.csv", index=False)

    # Mock artifacts
    (data_dir / "scaler.joblib").write_bytes(b"mock_scaler")
    (data_dir / "label_encoder.joblib").write_bytes(b"mock_encoder")
    with open(data_dir / "feature_list.json", "w") as f:
        json.dump({"features_after_selection": ["feat_1", "feat_2", "feat_3"]}, f)
    with open(data_dir / "label_mapping.json", "w") as f:
        json.dump({"label_mapping": {"BENIGN": "benign"}}, f)
    with open(data_dir / "preprocessing_report.json", "w") as f:
        json.dump({"status": "ok"}, f)

    return data_dir


def test_validator_passes_on_valid_data(valid_dataset_dir: Path):
    """Test validator reports complete pass on valid splits and artifacts."""
    validator = DataValidator(valid_dataset_dir)
    report = validator.validate()

    assert report.is_valid is True
    assert report.failed_checks == 0
    assert report.passed_checks >= 8
    assert len(report.errors) == 0


def test_validator_fails_missing_files(tmp_path: Path):
    """Test validator catches missing files and directories."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    validator = DataValidator(empty_dir)
    report = validator.validate()

    assert report.is_valid is False
    assert any("split_files_exist" in err for err in report.errors)


def test_validator_fails_on_nan(valid_dataset_dir: Path):
    """Test validator catches injected NaN values in features."""
    train_df = pd.read_csv(valid_dataset_dir / "train.csv")
    train_df.loc[0, "feat_1"] = np.nan
    train_df.to_csv(valid_dataset_dir / "train.csv", index=False)

    validator = DataValidator(valid_dataset_dir)
    report = validator.validate()

    assert report.is_valid is False
    assert any("no_nan_values" in err for err in report.errors)


def test_validator_fails_on_inf(valid_dataset_dir: Path):
    """Test validator catches injected Inf values in features."""
    val_df = pd.read_csv(valid_dataset_dir / "val.csv")
    val_df.loc[0, "feat_2"] = np.inf
    val_df.to_csv(valid_dataset_dir / "val.csv", index=False)

    validator = DataValidator(valid_dataset_dir)
    report = validator.validate()

    assert report.is_valid is False
    assert any("no_infinite_values" in err for err in report.errors)


def test_validator_fails_column_mismatch(valid_dataset_dir: Path):
    """Test validator detects column mismatch between splits."""
    test_df = pd.read_csv(valid_dataset_dir / "test.csv")
    test_df = test_df.drop(columns=["feat_3"])
    test_df.to_csv(valid_dataset_dir / "test.csv", index=False)

    validator = DataValidator(valid_dataset_dir)
    report = validator.validate()

    assert report.is_valid is False
    assert any("feature_columns_match" in err for err in report.errors)


def test_validator_fails_missing_artifacts(valid_dataset_dir: Path):
    """Test validator catches missing preprocessing artifacts."""
    (valid_dataset_dir / "scaler.joblib").unlink()

    validator = DataValidator(valid_dataset_dir)
    report = validator.validate()

    assert report.is_valid is False
    assert any("artifacts_exist" in err for err in report.errors)


def test_validation_report_export(tmp_path: Path, valid_dataset_dir: Path):
    """Test saving validation report to JSON and Markdown."""
    report = validate_processed_data(valid_dataset_dir)
    saved_files = report.save(tmp_path)

    assert Path(saved_files["json"]).exists()
    assert Path(saved_files["markdown"]).exists()

    md_content = Path(saved_files["markdown"]).read_text()
    assert "ASCCD Data Validation Report" in md_content
    assert "PASSED" in md_content
