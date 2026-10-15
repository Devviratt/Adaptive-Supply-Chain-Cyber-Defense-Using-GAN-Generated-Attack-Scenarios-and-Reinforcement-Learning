#!/usr/bin/env python3
"""
ASCCD Synthetic Attack Data Generation Script.

Loads a trained CTGAN checkpoint and generates realistic, conditioned attack scenarios.
Optionally validates generated data distributions against the real training baseline.

Usage:
    python scripts/generate_synthetic.py --num-samples 2000
    python scripts/generate_synthetic.py --conditional --num-samples 1500
    python scripts/generate_synthetic.py --validate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from src.common.logging import get_logger
from src.gan.generator import SyntheticAttackGenerator
from src.gan.validator import SyntheticDataValidator

logger = get_logger("generate_synthetic")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic cyber attack scenarios using trained CTGAN."
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("artifacts/models/ctgan/ctgan_model.pkl"),
        help="Path to trained CTGAN checkpoint (default: artifacts/models/ctgan/ctgan_model.pkl)",
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=Path("data/processed/train.csv"),
        help="Path to real training data for schema alignment and validation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/synthetic_attacks.csv"),
        help="Output CSV path for generated synthetic data",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=2000,
        help="Total synthetic samples to generate (default: 2000)",
    )
    parser.add_argument(
        "--conditional",
        action="store_true",
        help="Generate balanced attack classes conditionally",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Automatically validate generated synthetic data against training data",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for generation (default: 42)",
    )
    return parser.parse_args()


def main() -> int:
    """Execute synthetic data generation."""
    args = parse_args()

    print("=" * 60)
    print("ASCCD Phase 3 — Synthetic Attack Scenario Generation")
    print("=" * 60)

    if not args.model_path.exists():
        logger.error("model_checkpoint_not_found", path=str(args.model_path))
        print(f"Error: Model checkpoint not found at {args.model_path}")
        print("Please train CTGAN first: python scripts/train_gan.py")
        return 1

    generator = SyntheticAttackGenerator.from_checkpoint(args.model_path)
    print(f"Loaded CTGAN model from: {args.model_path}")
    print(f"Available training classes: {generator.valid_labels}")

    if args.conditional:
        # Balanced target distribution across known attack categories
        target_labels = [c for c in generator.valid_labels if c != "benign"]
        if not target_labels:
            target_labels = generator.valid_labels

        per_class = max(10, args.num_samples // len(target_labels))
        class_counts = {c: per_class for c in target_labels}
        print(f"Conditional generation targets: {class_counts}")
        synth_df = generator.generate_conditional(class_counts, seed=args.seed)
    else:
        synth_df = generator.generate(args.num_samples, seed=args.seed)

    # Save synthetic dataset
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generator.save_synthetic_data(synth_df, args.output)
    print(f"\nGenerated {len(synth_df):,} synthetic samples saved to: {args.output}")

    if "Label" in synth_df.columns:
        print("Generated class distribution:")
        for k, v in synth_df["Label"].value_counts().items():
            print(f"  - {k}: {v:,} ({v / len(synth_df):.1%})")

    # Optional validation
    if args.validate:
        if not args.train_data.exists():
            print(f"\nWarning: Training data not found at {args.train_data}, skipping validation.")
        else:
            print("\nRunning statistical validation against real training data...")
            real_train_df = pd.read_csv(args.train_data)
            validator = SyntheticDataValidator()
            summary = validator.validate(real_train_df, synth_df)

            reports_dir = Path("artifacts/reports")
            json_p, md_p = validator.export_reports(summary, reports_dir)
            print(f"Validation Status:          {summary.validation_status}")
            print(f"Mean Wasserstein Distance:  {summary.mean_wasserstein_distance:.4f}")
            print(f"Mean JS Divergence:         {summary.mean_js_divergence:.4f}")
            print(f"Correlation Similarity:     {summary.correlation_similarity:.4f}")
            print(f"Validation reports saved:   {json_p} and {md_p}")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
