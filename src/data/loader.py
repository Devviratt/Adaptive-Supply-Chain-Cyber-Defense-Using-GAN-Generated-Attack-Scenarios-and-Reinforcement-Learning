"""
ASCCD Data Loader — CIC-IDS2017 CSV ingestion.

Discovers, validates, and concatenates CIC-IDS2017 CSV files from
a specified directory. Reports per-file metadata and schema issues.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.common.logging import get_logger

logger = get_logger(__name__)

# ============================================================
# Expected CIC-IDS2017 CSV filenames (canonical set)
# ============================================================
EXPECTED_FILES = [
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
]


def discover_csv_files(input_dir: str | Path) -> list[Path]:
    """Discover CSV files in the input directory.

    Looks for .csv files. If known CIC-IDS2017 filenames are found,
    they are prioritized. Otherwise, all CSVs are included.

    Args:
        input_dir: Path to directory containing raw CSV files.

    Returns:
        Sorted list of CSV file paths.

    Raises:
        FileNotFoundError: If the input directory does not exist.
        ValueError: If no CSV files are found.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")
    if not input_path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_path}")

    csv_files = sorted(input_path.glob("*.csv"))

    if not csv_files:
        raise ValueError(
            f"No CSV files found in {input_path}. "
            f"Please download the CIC-IDS2017 dataset and place CSV files here. "
            f"See docs/setup.md for instructions."
        )

    # Check which expected files are present/missing
    found_names = {f.name for f in csv_files}
    expected_found = [name for name in EXPECTED_FILES if name in found_names]
    expected_missing = [name for name in EXPECTED_FILES if name not in found_names]

    logger.info(
        "csv_discovery_complete",
        total_csv_files=len(csv_files),
        expected_files_found=len(expected_found),
        expected_files_missing=len(expected_missing),
        missing_files=expected_missing if expected_missing else None,
    )

    return csv_files


def _detect_label_column(columns: list[str]) -> str | None:
    """Detect the label column, handling CIC-IDS2017's leading-space quirk.

    CIC-IDS2017 CSVs commonly have ' Label' (with leading space) as the
    column name. Some cleaned versions use 'Label'.

    Returns:
        The actual column name, or None if not found.
    """
    for col in columns:
        if col.strip().lower() == "label":
            return col
    return None


def load_single_csv(
    filepath: Path,
    label_column: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a single CSV file with metadata collection.

    Args:
        filepath: Path to the CSV file.
        label_column: Expected label column name (detected if None).

    Returns:
        Tuple of (DataFrame, metadata_dict).

    Raises:
        ValueError: If the file cannot be read or has critical issues.
    """
    metadata: dict[str, Any] = {
        "filename": filepath.name,
        "filepath": str(filepath),
        "status": "ok",
        "warnings": [],
    }

    try:
        df = pd.read_csv(
            filepath,
            encoding="utf-8",
            low_memory=False,
            na_values=["", "NA", "N/A", "NaN", "nan", "null", "None"],
        )
    except Exception as e:
        metadata["status"] = "error"
        metadata["error"] = str(e)
        logger.error("csv_load_failed", filename=filepath.name, error=str(e))
        raise ValueError(f"Failed to load {filepath.name}: {e}") from e

    metadata["rows"] = len(df)
    metadata["columns"] = len(df.columns)
    metadata["column_names"] = list(df.columns)
    metadata["size_mb"] = round(filepath.stat().st_size / (1024 * 1024), 2)

    # Strip whitespace from column names (CIC-IDS2017 quirk)
    original_cols = list(df.columns)
    df.columns = df.columns.str.strip()
    renamed = [
        (orig, new) for orig, new in zip(original_cols, df.columns, strict=True) if orig != new
    ]
    if renamed:
        metadata["warnings"].append(f"Stripped whitespace from {len(renamed)} column name(s)")

    # Detect label column
    detected_label = _detect_label_column(list(df.columns))
    if detected_label and detected_label != "Label":
        df = df.rename(columns={detected_label: "Label"})
        metadata["warnings"].append(f"Renamed label column '{detected_label}' → 'Label'")

    if "Label" in df.columns:
        # Strip whitespace from label values
        df["Label"] = df["Label"].astype(str).str.strip()
        label_counts = df["Label"].value_counts().to_dict()
        metadata["label_distribution"] = label_counts
    else:
        metadata["warnings"].append("No label column detected")

    # Check for duplicate column names
    dup_cols = df.columns[df.columns.duplicated()].tolist()
    if dup_cols:
        metadata["warnings"].append(f"Duplicate columns found: {dup_cols}")
        metadata["status"] = "warning"

    logger.info(
        "csv_loaded",
        filename=filepath.name,
        rows=metadata["rows"],
        columns=metadata["columns"],
        size_mb=metadata["size_mb"],
        warnings=metadata["warnings"] if metadata["warnings"] else None,
    )

    return df, metadata


def load_dataset(
    input_dir: str | Path,
    sample_size: int | None = None,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and concatenate all CIC-IDS2017 CSV files from a directory.

    Args:
        input_dir: Path to directory containing raw CSV files.
        sample_size: If set, return a random sample of this many rows.
        random_seed: Random seed for reproducible sampling.

    Returns:
        Tuple of (concatenated DataFrame, dataset metadata dict).

    Raises:
        FileNotFoundError: If input directory doesn't exist.
        ValueError: If no valid CSV files can be loaded.
    """
    csv_files = discover_csv_files(input_dir)

    frames: list[pd.DataFrame] = []
    file_metadata: list[dict[str, Any]] = []
    errors: list[str] = []

    for filepath in csv_files:
        try:
            df, meta = load_single_csv(filepath)
            frames.append(df)
            file_metadata.append(meta)
        except ValueError as e:
            errors.append(str(e))
            logger.warning("csv_skipped", filename=filepath.name, error=str(e))

    if not frames:
        raise ValueError(f"No CSV files could be loaded from {input_dir}. " f"Errors: {errors}")

    # Concatenate — check for schema consistency
    reference_cols = set(frames[0].columns)
    schema_warnings: list[str] = []

    for _i, (df, meta) in enumerate(zip(frames[1:], file_metadata[1:], strict=True), start=1):
        current_cols = set(df.columns)
        extra = current_cols - reference_cols
        missing = reference_cols - current_cols

        if extra:
            schema_warnings.append(
                f"{meta['filename']}: has {len(extra)} extra column(s): {sorted(extra)[:5]}"
            )
        if missing:
            schema_warnings.append(
                f"{meta['filename']}: missing {len(missing)} column(s): {sorted(missing)[:5]}"
            )

    # Use concat with join="outer" to handle schema differences
    combined = pd.concat(frames, ignore_index=True, sort=False)

    dataset_metadata: dict[str, Any] = {
        "total_files_found": len(csv_files),
        "files_loaded": len(frames),
        "files_failed": len(errors),
        "total_rows": len(combined),
        "total_columns": len(combined.columns),
        "column_names": list(combined.columns),
        "schema_warnings": schema_warnings if schema_warnings else None,
        "file_details": file_metadata,
        "errors": errors if errors else None,
        "sample_applied": False,
    }

    # Apply sampling if requested
    if sample_size and sample_size < len(combined):
        combined = combined.sample(n=sample_size, random_state=random_seed).reset_index(drop=True)
        dataset_metadata["sample_applied"] = True
        dataset_metadata["sample_size"] = sample_size
        dataset_metadata["sample_seed"] = random_seed

    # Report label distribution of combined dataset
    if "Label" in combined.columns:
        dataset_metadata["label_distribution"] = combined["Label"].value_counts().to_dict()

    logger.info(
        "dataset_loaded",
        files_loaded=len(frames),
        total_rows=len(combined),
        total_columns=len(combined.columns),
        sample_applied=dataset_metadata["sample_applied"],
    )

    return combined, dataset_metadata
