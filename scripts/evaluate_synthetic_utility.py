#!/usr/bin/env python3
"""
ASCCD Downstream Utility Evaluation CLI.

Executes a controlled empirical experiment evaluating downstream cyber attack detection
on the untouched real test dataset:
  - Model A: Trained exclusively on real training samples.
  - Model B: Trained on real training data augmented with validated synthetic samples.

Usage:
    python scripts/evaluate_synthetic_utility.py
    python scripts/evaluate_synthetic_utility.py --synthetic-data data/generated/synthetic_attacks.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from src.common.logging import get_logger
from src.gan.evaluation import DownstreamUtilityEvaluator

logger = get_logger("evaluate_synthetic_utility")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run controlled downstream ML utility experiment comparing real vs augmented training."
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=Path("data/processed/train.csv"),
        help="Path to real training data (default: data/processed/train.csv)",
    )
    parser.add_argument(
        "--synthetic-data",
        type=Path,
        default=Path("data/generated/synthetic_attacks.csv"),
        help="Path to synthetic attack data (default: data/generated/synthetic_attacks.csv)",
    )
    parser.add_argument(
        "--test-data",
        type=Path,
        default=Path("data/processed/test.csv"),
        help="Path to untouched real test data (default: data/processed/test.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/reports"),
        help="Directory to export utility evaluation reports (default: artifacts/reports)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for classifier training (default: 42)",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in RandomForest classifiers (default: 100)",
    )
    return parser.parse_args()


def main() -> int:
    """Execute downstream utility experiment."""
    args = parse_args()

    print("=" * 60)
    print("ASCCD Phase 3 — Downstream ML Utility Controlled Experiment")
    print("=" * 60)

    for path, name in [
        (args.train_data, "Real Training Data"),
        (args.synthetic_data, "Synthetic Data"),
        (args.test_data, "Real Test Data"),
    ]:
        if not path.exists():
            print(f"Error: {name} not found at {path}")
            return 1

    print("Loading datasets:")
    print(f"  - Real Train:      {args.train_data}")
    print(f"  - Synthetic Train: {args.synthetic_data}")
    print(f"  - Untouched Test:  {args.test_data}")

    real_train_df = pd.read_csv(args.train_data)
    synthetic_df = pd.read_csv(args.synthetic_data)
    real_test_df = pd.read_csv(args.test_data)

    print("\nDataset Dimensions:")
    print(f"  - Real Train:      {real_train_df.shape[0]:,} rows × {real_train_df.shape[1]} cols")
    print(f"  - Synthetic Train: {synthetic_df.shape[0]:,} rows × {synthetic_df.shape[1]} cols")
    print(f"  - Untouched Test:  {real_test_df.shape[0]:,} rows × {real_test_df.shape[1]} cols")

    evaluator = DownstreamUtilityEvaluator(random_state=args.seed, n_estimators=args.n_estimators)

    print("\nTraining Model A (Real Only) and Model B (Augmented) & Evaluating on Test Set...")
    report = evaluator.evaluate_utility(real_train_df, synthetic_df, real_test_df)

    # Export reports
    json_path, md_path = evaluator.export_reports(report, args.output_dir)

    print("\n" + "=" * 60)
    print("DOWNSTREAM EXPERIMENT RESULTS SUMMARY")
    print("=" * 60)
    print(f"Model A (Real Only) Macro-F1:   {report.model_a_real_only.macro_f1:.4f}")
    print(f"Model B (Augmented) Macro-F1:   {report.model_b_augmented.macro_f1:.4f}")
    print(f"Macro-F1 Delta:                 {report.macro_f1_delta:+.4f}")
    print(f"Accuracy Delta:                 {report.accuracy_delta:+.4f}")
    print(
        f"Augmentation Verdict:           {'BENEFICIAL / ACCEPTABLE' if report.augmentation_utility_positive else 'DEGRADED'}"
    )
    print("\nPer-Class F1 Deltas:")
    for cls, delta in report.minority_class_f1_improvements.items():
        print(
            f"  - {cls:15s}: {delta:+.4f} (Support: {report.model_a_real_only.per_class_support.get(cls, 0)})"
        )
    print("\nReports saved to:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
