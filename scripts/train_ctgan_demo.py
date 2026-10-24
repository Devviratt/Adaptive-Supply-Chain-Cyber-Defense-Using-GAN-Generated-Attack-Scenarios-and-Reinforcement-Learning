#!/usr/bin/env python3
"""Train CTGAN, generate synthetic rows, or validate a generated dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_yaml_config
from src.gan.ctgan import (
    available_output_path,
    generate_ctgan,
    train_ctgan,
    validate_synthetic,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train", "generate", "validate"])
    parser.add_argument("--input", default=str(PROJECT_ROOT / "data/processed/train.csv"))
    parser.add_argument("--output", default=None)
    parser.add_argument("--model", default=str(PROJECT_ROOT / "artifacts/models/ctgan/model.pkl"))
    parser.add_argument("--report", default=None)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config/gan.yaml"))
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--per-class", help='JSON class counts, e.g. {"dos":100,"benign":100}')
    args = parser.parse_args()

    config = load_yaml_config(Path(args.config))
    settings = config.get("ctgan", {})
    if args.epochs is not None:
        settings["epochs"] = args.epochs
    if args.seed is not None:
        settings["seed"] = args.seed
    if args.command == "train":
        metadata = train_ctgan(args.input, args.model, config)
        print(json.dumps(metadata, indent=2))
    elif args.command == "generate":
        generation = settings.get("generation", {})
        count = args.count or int(generation.get("num_samples", 2000))
        per_class = json.loads(args.per_class) if args.per_class else None
        output_path = available_output_path(
            args.output or PROJECT_ROOT / "data/generated/ctgan_samples.csv"
        )
        generated = generate_ctgan(
            args.model,
            output_path,
            count,
            args.seed or int(settings.get("seed", 42)),
            per_class=per_class,
        )
        print(f"Generated {len(generated):,} synthetic rows: {output_path}")
    else:
        generated_path = Path(args.output) if args.output else _latest_generated_file()
        report_path = available_output_path(
            args.report or generated_path.with_name(f"{generated_path.stem}_validation.json")
        )
        report = validate_synthetic(args.input, generated_path, report_path)
        print(json.dumps(report, indent=2))


def _latest_generated_file() -> Path:
    """Find the most recently modified CTGAN sample for validation."""
    candidates = (PROJECT_ROOT / "data/generated").glob("ctgan_samples*.csv")
    latest = max(candidates, key=lambda path: path.stat().st_mtime, default=None)
    if latest is None:
        raise FileNotFoundError(
            "No CTGAN sample found. Generate one first or pass --output <sample.csv>."
        )
    return latest


if __name__ == "__main__":
    main()
