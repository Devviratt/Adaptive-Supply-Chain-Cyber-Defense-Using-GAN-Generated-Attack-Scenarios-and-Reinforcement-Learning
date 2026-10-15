#!/usr/bin/env python3
"""
ASCCD CTGAN Training Script.

Trains a Conditional Tabular GAN (CTGAN) on processed CIC-IDS2017 training features.
Ensures zero data leakage: uses data/processed/train.csv exclusively.

Usage:
    python scripts/train_gan.py
    python scripts/train_gan.py --epochs 200 --batch-size 500
    python scripts/train_gan.py --dev-mode
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml
from src.common.logging import get_logger
from src.gan.trainer import CTGANTrainer

logger = get_logger("train_gan")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train CTGAN model on processed cybersecurity training data."
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=Path("data/processed/train.csv"),
        help="Path to processed training dataset (default: data/processed/train.csv)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/gan.yaml"),
        help="Path to CTGAN configuration YAML (default: config/gan.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/models/ctgan"),
        help="Directory to save model checkpoint and metadata",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override batch size",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Run in fast development mode (fewer epochs)",
    )
    return parser.parse_args()


def main() -> int:
    """Execute CTGAN training pipeline."""
    args = parse_args()

    print("=" * 60)
    print("ASCCD Phase 3 — CTGAN Attack Scenario Training")
    print("=" * 60)

    if not args.train_data.exists():
        logger.error("train_data_not_found", path=str(args.train_data))
        print(f"Error: Training data not found at {args.train_data}")
        print("Please run Phase 2 preprocessing first: python scripts/preprocess.py")
        return 1

    print(f"Loading training data from: {args.train_data}")
    train_df = pd.read_csv(args.train_data)
    print(f"Training partition shape: {train_df.shape[0]:,} rows, {train_df.shape[1]} columns")

    # Load configuration
    cfg: dict = {}
    if args.config.exists():
        with open(args.config) as f:
            cfg = yaml.safe_load(f) or {}

    ctgan_cfg = cfg.get("ctgan", {})
    epochs = args.epochs
    if epochs is None:
        if args.dev_mode:
            epochs = ctgan_cfg.get("dev_mode", {}).get("epochs", 50)
            print(f"Development mode enabled: training for {epochs} epochs")
        else:
            epochs = ctgan_cfg.get("epochs", 300)

    batch_size = args.batch_size or ctgan_cfg.get("batch_size", 500)

    # Initialize trainer
    trainer = CTGANTrainer(
        config=cfg,
        seed=args.seed,
        epochs=epochs,
        batch_size=batch_size,
    )

    print(
        f"Starting CTGAN training (epochs={epochs}, batch_size={trainer.batch_size}, seed={args.seed})..."
    )
    trainer.fit(train_df, discrete_columns=["Label"])

    # Save artifacts
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "ctgan_model.pkl"
    meta_path = args.output_dir / "training_metadata.json"

    trainer.save(model_path, meta_path)

    print(f"\nModel checkpoint saved: {model_path}")
    print(f"Metadata report saved:  {meta_path}")
    if trainer.report:
        print(f"Training duration:      {trainer.report.training_duration_seconds:.2f}s")
        print(f"Classes modeled:        {trainer.report.classes_present}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
