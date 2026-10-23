#!/usr/bin/env python3
"""
ASCCD Dataset Preprocessing CLI.

Provides command-line interfaces for:
1. Raw dataset inspection: schema analysis, row counts, label distribution
2. Complete preprocessing pipeline: cleaning, encoding, feature selection,
   stratified splitting, and artifact export
3. Post-processing validation: automated check of schema, NaN/Inf absence,
   and split integrity
4. Distribution plots: clean, publication-ready class and split distribution charts

Usage:
    python scripts/preprocess.py --help
    python scripts/preprocess.py --inspect
    python scripts/preprocess.py --sample 50000
    python scripts/preprocess.py --input data/raw --output data/processed
    python scripts/preprocess.py --validate

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_yaml_config
from src.common.logging import get_logger
from src.data.loader import discover_csv_files, load_dataset
from src.data.preprocessor import DataPreprocessor
from src.data.splitter import stratified_split
from src.data.validator import validate_processed_data

logger = get_logger(__name__)


def generate_distribution_charts(
    output_dir: Path,
    train_dist: dict[str, int],
    val_dist: dict[str, int],
    test_dist: dict[str, int],
) -> None:
    """Generate clean, publication-ready distribution charts using matplotlib."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib_not_installed_skipping_charts")
        return

    # 1. Overall and split distribution chart
    all_classes = sorted(set(train_dist.keys()) | set(val_dist.keys()) | set(test_dist.keys()))
    if not all_classes:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(all_classes))
    width = 0.25

    train_vals = [train_dist.get(c, 0) for c in all_classes]
    val_vals = [val_dist.get(c, 0) for c in all_classes]
    test_vals = [test_dist.get(c, 0) for c in all_classes]

    ax.bar([i - width for i in x], train_vals, width, label="Train", color="#1f77b4")
    ax.bar(x, val_vals, width, label="Validation", color="#ff7f0e")
    ax.bar([i + width for i in x], test_vals, width, label="Test", color="#2ca02c")

    ax.set_yscale("log")
    ax.set_ylabel("Log Sample Count")
    ax.set_title("ASCCD CIC-IDS2017 Stratified Class Distribution Across Splits")
    ax.set_xticks(list(x))
    ax.set_xticklabels(all_classes, rotation=45, ha="right", fontsize=9)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    chart_path = output_dir / "class_distribution_splits.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    logger.info("chart_saved", path=str(chart_path))


def inspect_raw_dataset(input_dir: Path) -> None:
    """Inspect raw CSV files and output detailed summary."""
    print("=" * 70)
    print(f"ASCCD RAW DATASET INSPECTION: {input_dir}")
    print("=" * 70)

    try:
        csv_files = discover_csv_files(input_dir)
    except Exception as e:
        print(f"ERROR: Could not discover files: {e}")
        sys.exit(1)

    print(f"Found {len(csv_files)} CSV files:")
    import pandas as pd

    total_rows = 0

    for f in csv_files:
        try:
            # Read first 100 rows to check columns quickly
            sample_df = pd.read_csv(f, nrows=100)
            clean_cols = [c.strip() for c in sample_df.columns]
            label_col = (
                "Label"
                if "Label" in clean_cols
                else (" Label" if " Label" in sample_df.columns else None)
            )

            # Count total rows
            with open(f, "rb") as fp:
                row_count = sum(1 for _ in fp) - 1
            total_rows += row_count
            size_mb = f.stat().st_size / (1024 * 1024)

            print(f"\nFile: {f.name}")
            print(
                f"   Size: {size_mb:.2f} MB | Approx Rows: {row_count:,} | Columns: {len(sample_df.columns)}"
            )
            print(f"   Label column found: {label_col is not None}")
        except Exception as e:
            print(f"   WARNING: Could not inspect {f.name}: {e}")

    print("\n" + "=" * 70)
    print(f"Total Raw Files: {len(csv_files)} | Total Approx Rows: {total_rows:,}")
    print("=" * 70)


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    config_path: Path,
    sample_size: int | None = None,
    random_seed: int = 42,
    save_parquet: bool = True,
) -> None:
    """Run the complete end-to-end data preprocessing pipeline."""
    print("=" * 70)
    print("ASCCD: DATA PREPROCESSING PIPELINE (PHASE 2)")
    print("=" * 70)
    print(f"Input Directory:  {input_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"Config File:      {config_path}")
    print(f"Sample Size:      {sample_size or 'Full Dataset'}")
    print(f"Random Seed:      {random_seed}")
    print("=" * 70)

    # 1. Load config
    cfg = load_yaml_config(config_path) if config_path.exists() else {}
    prep_cfg = cfg.get("preprocessing", {})

    train_ratio = prep_cfg.get("train_ratio", 0.70)
    val_ratio = prep_cfg.get("val_ratio", 0.15)
    test_ratio = prep_cfg.get("test_ratio", 0.15)
    label_col = prep_cfg.get("label_column", "Label").strip()

    # 2. Ingest raw CSV files
    print("\n[Step 1/6] Ingesting and concatenating raw CSV files...")
    raw_df, dataset_meta = load_dataset(
        input_dir=input_dir,
        sample_size=sample_size,
        random_seed=random_seed,
    )
    print(f"Loaded {len(raw_df):,} total rows across {dataset_meta['files_loaded']} file(s).")

    # 3. Clean and normalize data (initial pass for labels & inf/nan before split)
    print("\n[Step 2/6] Initializing DataPreprocessor and normalizing schema...")
    preprocessor = DataPreprocessor(config=prep_cfg)

    # Clean raw dataframe (whitespace stripping, invalid drops, label normalization)
    cleaned_df = preprocessor.prepare_raw(raw_df)
    print(
        f"Cleaned dataset: {len(cleaned_df):,} rows remaining after deduplication and basic cleaning."
    )
    print("Normalized Class Distribution:")
    for k, v in cleaned_df[label_col].value_counts().items():
        print(f"  - {k}: {v:,}")

    # 4. Stratified Train / Validation / Test Split (BEFORE fit to prevent leakage)
    print(
        f"\n[Step 3/6] Performing Stratified Split ({train_ratio*100:.0f}% / {val_ratio*100:.0f}% / {test_ratio*100:.0f}%)..."
    )
    train_df, val_df, test_df, split_stats = stratified_split(
        df=cleaned_df,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        label_column=label_col,
        random_seed=random_seed,
    )
    print(
        f"Split sizes -> Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}"
    )

    # 5. Fit Preprocessor ONLY ON TRAIN, then transform all sets
    print(
        "\n[Step 4/6] Fitting transformations (variance threshold, correlation filter, scaler) on TRAIN only..."
    )
    train_processed, val_processed, test_processed = preprocessor.fit_transform_splits(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        label_column=label_col,
    )

    final_feature_count = len(train_processed.columns) - 1
    print(
        f"Feature processing complete. Retained {final_feature_count} features (dropped {len(preprocessor.report.features_removed_variance) + len(preprocessor.report.features_removed_correlation)} redundant/collinear features)."
    )

    # 6. Save splits and artifacts
    print(f"\n[Step 5/6] Exporting processed datasets and pipeline artifacts to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.csv"
    val_path = output_dir / "val.csv"
    test_path = output_dir / "test.csv"

    train_processed.to_csv(train_path, index=False)
    val_processed.to_csv(val_path, index=False)
    test_processed.to_csv(test_path, index=False)

    if save_parquet:
        try:
            train_processed.to_parquet(output_dir / "train.parquet", index=False)
            val_processed.to_parquet(output_dir / "val.parquet", index=False)
            test_processed.to_parquet(output_dir / "test.parquet", index=False)
            print("  Parquet files exported successfully.")
        except Exception as e:
            print(f"  Parquet export skipped: {e}")

    # Save preprocessor artifacts
    preprocessor.save_artifacts(output_dir)

    # Save split statistics
    split_stats_path = output_dir / "split_statistics.json"
    split_stats.save(split_stats_path)

    # Save dataset metadata
    dataset_meta_path = output_dir / "dataset_metadata.json"
    with open(dataset_meta_path, "w", encoding="utf-8") as f:
        json.dump(dataset_meta, f, indent=2, default=str)

    # Generate charts
    generate_distribution_charts(
        output_dir=output_dir,
        train_dist=split_stats.train_class_distribution,
        val_dist=split_stats.val_class_distribution,
        test_dist=split_stats.test_class_distribution,
    )

    # 7. Automated Validation
    print("\n[Step 6/6] Running DataValidator verification suite on exported outputs...")
    val_report = validate_processed_data(data_dir=output_dir, expected_label_col=label_col)
    val_report.save(output_dir)

    print("\n" + "=" * 70)
    print("PREPROCESSING PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Status:            {'SUCCESS (Validated)' if val_report.is_valid else 'FAILED'}")
    print(f"Total Rows Ingest: {dataset_meta['total_rows']:,}")
    print(f"Rows After Clean:  {len(cleaned_df):,}")
    print(f"Train Set Rows:    {len(train_processed):,}")
    print(f"Val Set Rows:      {len(val_processed):,}")
    print(f"Test Set Rows:     {len(test_processed):,}")
    print(f"Original Features: {preprocessor.report.original_feature_count}")
    print(f"Final Features:    {final_feature_count}")
    print(f"Classes Mapped:    {len(preprocessor.valid_labels)}")
    print(f"Validation Checks: {val_report.passed_checks}/{val_report.total_checks} passed")
    print(f"Artifacts Saved In: {output_dir}")
    print("=" * 70)

    if not val_report.is_valid:
        print("ERROR: Pipeline completed with validation errors:")
        for err in val_report.errors:
            print(f"   - {err}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="ASCCD Data Preprocessing & Validation CLI for CIC-IDS2017."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw"),
        help="Path to directory with raw CIC-IDS2017 CSV files (default: data/raw).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed"),
        help="Path to directory to write processed splits and artifacts (default: data/processed).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(PROJECT_ROOT / "config" / "preprocessing.yaml"),
        help="Path to preprocessing YAML configuration file.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="If set, downsamples input to N rows for fast development/testing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible shuffling and splitting (default: 42).",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Inspect raw CSV files in input directory and display schema info.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validator against an existing processed data directory.",
    )

    args = parser.parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    config_path = Path(args.config)

    if args.inspect:
        inspect_raw_dataset(input_dir)
        return

    if args.validate:
        print(f"Running validation on: {output_dir}")
        report = validate_processed_data(output_dir)
        report.save(output_dir)
        print(report.to_markdown())
        if not report.is_valid:
            sys.exit(1)
        return

    # Check input directory exists and has files
    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        print(
            "Run `python scripts/download_dataset.py --generate-dev-sample` to create a dev sample."
        )
        sys.exit(1)

    csv_files = list(input_dir.glob("*.csv"))
    if not csv_files:
        print(f"ERROR: No CSV files found in: {input_dir}")
        print(
            "Run `python scripts/download_dataset.py --generate-dev-sample` to create a dev sample."
        )
        sys.exit(1)

    run_pipeline(
        input_dir=input_dir,
        output_dir=output_dir,
        config_path=config_path,
        sample_size=args.sample,
        random_seed=args.seed,
    )


if __name__ == "__main__":
    main()
