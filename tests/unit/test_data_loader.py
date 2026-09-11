"""
Unit tests for ASCCD Data Loader (src/data/loader.py).

Tests file discovery, CSV loading, column stripping, label detection,
missing directory handling, and dataset concatenation with sampling.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data.loader import discover_csv_files, load_dataset, load_single_csv


@pytest.fixture
def mock_csv_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with mock CIC-IDS2017 CSV files."""
    data_dir = tmp_path / "raw_data"
    data_dir.mkdir()

    # File 1: Standard benign and dos
    df1 = pd.DataFrame(
        {
            " Flow Duration": [100, 200, 300, 400],
            " Total Fwd Packets": [10, 20, 30, 40],
            " Flow Bytes/s": [1.5, 2.5, np.inf, 4.5],  # Contains inf
            " Label": ["BENIGN", "BENIGN", "DoS Hulk", "BENIGN"],
        }
    )
    df1.to_csv(data_dir / "Monday-WorkingHours.pcap_ISCX.csv", index=False)

    # File 2: Additional attacks with leading spaces in headers
    df2 = pd.DataFrame(
        {
            " Flow Duration": [500, 600, 700],
            " Total Fwd Packets": [50, 60, 70],
            " Flow Bytes/s": [5.5, np.nan, 7.5],  # Contains nan
            " Label": ["PortScan", "DDoS", "BENIGN"],
        }
    )
    df2.to_csv(data_dir / "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv", index=False)

    return data_dir


def test_discover_csv_files_success(mock_csv_dir: Path):
    """Test discovering CSV files in directory."""
    files = discover_csv_files(mock_csv_dir)
    assert len(files) == 2
    filenames = [f.name for f in files]
    assert "Monday-WorkingHours.pcap_ISCX.csv" in filenames
    assert "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv" in filenames


def test_discover_csv_files_nonexistent_dir(tmp_path: Path):
    """Test error raised for non-existent directory."""
    with pytest.raises(FileNotFoundError):
        discover_csv_files(tmp_path / "non_existent")


def test_discover_csv_files_empty_dir(tmp_path: Path):
    """Test error raised when no CSV files exist."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No CSV files found"):
        discover_csv_files(empty_dir)


def test_load_single_csv(mock_csv_dir: Path):
    """Test loading a single CSV file, checking whitespace stripping and label renaming."""
    file_path = mock_csv_dir / "Monday-WorkingHours.pcap_ISCX.csv"
    df, meta = load_single_csv(file_path)

    assert len(df) == 4
    # Columns should be stripped of leading/trailing spaces
    assert "Flow Duration" in df.columns
    assert "Total Fwd Packets" in df.columns
    assert "Label" in df.columns
    assert meta["status"] == "ok"
    assert meta["rows"] == 4
    assert "BENIGN" in meta["label_distribution"]


def test_load_single_csv_malformed(tmp_path: Path):
    """Test loading an unreadable/malformed CSV file."""
    bad_file = tmp_path / "corrupt.csv"
    bad_file.write_bytes(b"\x80\x81\x82\x83\n")

    with pytest.raises(ValueError, match="Failed to load"):
        load_single_csv(bad_file)


def test_load_dataset_concatenation(mock_csv_dir: Path):
    """Test full dataset loading and concatenation."""
    df, meta = load_dataset(mock_csv_dir)

    assert meta["files_loaded"] == 2
    assert meta["total_rows"] == 7
    assert len(df) == 7
    assert "Label" in df.columns
    assert set(df["Label"].unique()) == {"BENIGN", "DoS Hulk", "PortScan", "DDoS"}


def test_load_dataset_with_sampling(mock_csv_dir: Path):
    """Test loading dataset with sample_size constraint."""
    df, meta = load_dataset(mock_csv_dir, sample_size=3, random_seed=42)

    assert len(df) == 3
    assert meta["sample_applied"] is True
    assert meta["sample_size"] == 3
