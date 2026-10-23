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
from src.gan.ctgan import generate_ctgan, train_ctgan, validate_synthetic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train", "generate", "validate"])
    parser.add_argument("--input", default=str(PROJECT_ROOT / "data/processed/train.csv"))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "data/generated/ctgan_samples.csv"))
    parser.add_argument("--model", default=str(PROJECT_ROOT / "artifacts/models/ctgan/model.pkl"))
    parser.add_argument("--report", default=str(PROJECT_ROOT / "data/generated/ctgan_validation.json"))
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
        generated = generate_ctgan(args.model, args.output, count, args.seed or int(settings.get("seed", 42)), per_class=per_class)
        print(f"Generated {len(generated):,} synthetic rows: {args.output}")
    else:
        report = validate_synthetic(args.input, args.output, args.report)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
