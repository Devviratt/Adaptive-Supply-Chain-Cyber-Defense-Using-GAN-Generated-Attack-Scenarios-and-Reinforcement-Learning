#!/usr/bin/env python3
"""Create a memory-bounded, stratified CIC-IDS2017 sample for training."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_yaml_config
from src.data.loader import discover_csv_files
from src.data.preprocessor import DataPreprocessor


def allocate_sample_quotas(
    class_counts: dict[str, int],
    sample_size: int,
    minimum_per_class: int,
) -> dict[str, int]:
    """Allocate an exact sample size proportionally, with a rare-class floor."""
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    if minimum_per_class < 0:
        raise ValueError("minimum_per_class cannot be negative")
    if any(count < 0 for count in class_counts.values()):
        raise ValueError("class counts cannot be negative")

    available = {label: count for label, count in class_counts.items() if count > 0}
    total_available = sum(available.values())
    if sample_size > total_available:
        raise ValueError(
            f"Requested {sample_size} rows but only {total_available} cleaned rows are available"
        )

    quotas = {label: min(count, minimum_per_class) for label, count in available.items()}
    remaining = sample_size - sum(quotas.values())

    while remaining:
        capacity = {label: available[label] - quotas[label] for label in available}
        total_capacity = sum(capacity.values())
        if remaining > total_capacity:
            raise ValueError("Cannot allocate the requested sample size without replacement")

        shares = {label: remaining * count / total_capacity for label, count in capacity.items()}
        additions = {label: min(capacity[label], int(shares[label])) for label in capacity}
        for label, amount in additions.items():
            quotas[label] += amount
        remaining -= sum(additions.values())
        if not remaining:
            break

        order = sorted(
            available,
            key=lambda label: (shares[label] - int(shares[label]), label),
            reverse=True,
        )
        progressed = False
        for label in order:
            if remaining and quotas[label] < available[label]:
                quotas[label] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            raise ValueError("Unable to allocate sample quotas")

    return quotas


def _prepare_chunk(
    frame: pd.DataFrame,
    preprocessor: DataPreprocessor,
    seen_hashes: set[int],
    expected_columns: list[str] | None,
) -> tuple[pd.DataFrame, list[str]]:
    """Normalize schema and clean one chunk while deduplicating across chunks."""
    frame.columns = frame.columns.str.strip()
    if expected_columns is None:
        expected_columns = list(frame.columns)
    elif set(frame.columns) != set(expected_columns):
        raise ValueError("CIC-IDS2017 CSV files do not have a consistent column schema")
    else:
        frame = frame[expected_columns]

    label_columns = [column for column in frame.columns if column.lower() == "label"]
    if len(label_columns) != 1:
        raise ValueError(f"Expected one label column; found {label_columns}")
    if label_columns[0] != "Label":
        frame = frame.rename(columns={label_columns[0]: "Label"})

    frame = preprocessor.drop_configured_columns(frame)
    row_hashes = pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype=np.uint64)
    keep = np.zeros(len(frame), dtype=bool)
    for index, value in enumerate(row_hashes):
        key = int(value)
        if key not in seen_hashes:
            seen_hashes.add(key)
            keep[index] = True

    cleaned = preprocessor.clean(frame.loc[keep])
    return cleaned, expected_columns


def _iter_clean_chunks(
    input_dir: Path,
    preprocessor: DataPreprocessor,
    chunk_size: int,
    seen_hashes: set[int],
):
    expected_columns = None
    for path in discover_csv_files(input_dir):
        for frame in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
            cleaned, expected_columns = _prepare_chunk(
                frame,
                preprocessor,
                seen_hashes,
                expected_columns,
            )
            yield cleaned


def create_sample(
    input_dir: Path,
    output_path: Path,
    config_path: Path,
    sample_size: int = 71429,
    minimum_per_class: int = 500,
    chunk_size: int = 25000,
    seed: int = 42,
) -> dict[str, Any]:
    """Stream, clean, and stratify source rows without loading the archive at once."""
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing sample: {output_path}")
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    config = load_yaml_config(config_path)
    prep_config = config.get("preprocessing", config)
    preprocessor = DataPreprocessor(prep_config)

    class_counts: Counter[str] = Counter()
    unique_rows = 0
    for cleaned in _iter_clean_chunks(
        input_dir,
        preprocessor,
        chunk_size,
        seen_hashes=set(),
    ):
        unique_rows += len(cleaned)
        labels = preprocessor.normalize_labels(cleaned[["Label"]].copy())["Label"]
        class_counts.update(labels.value_counts().to_dict())

    quotas = allocate_sample_quotas(
        dict(class_counts),
        sample_size=sample_size,
        minimum_per_class=minimum_per_class,
    )
    rng = np.random.default_rng(seed)
    reservoirs: dict[str, pd.DataFrame] = {}
    seen_hashes: set[int] = set()

    for cleaned in _iter_clean_chunks(
        input_dir,
        preprocessor,
        chunk_size,
        seen_hashes=seen_hashes,
    ):
        labels = preprocessor.normalize_labels(cleaned[["Label"]].copy())["Label"]
        for label, indices in labels.groupby(labels, sort=False).groups.items():
            quota = quotas.get(str(label), 0)
            if not quota:
                continue
            candidates = cleaned.loc[indices].copy()
            candidates["_sample_priority"] = rng.random(len(candidates))
            if label in reservoirs:
                candidates = pd.concat(
                    [reservoirs[str(label)], candidates],
                    ignore_index=True,
                )
            reservoirs[str(label)] = candidates.nsmallest(
                quota,
                "_sample_priority",
            )

    sampled = pd.concat(reservoirs.values(), ignore_index=True)
    sampled = sampled.drop(columns="_sample_priority")
    sampled = sampled.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    if len(sampled) != sample_size:
        raise RuntimeError(f"Sampling produced {len(sampled)} rows; expected exactly {sample_size}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_csv(output_path, index=False)
    metadata = {
        "source_directory": str(input_dir),
        "source_files": [path.name for path in discover_csv_files(input_dir)],
        "sample_path": str(output_path),
        "source_unique_clean_rows": unique_rows,
        "sample_rows": len(sampled),
        "source_class_distribution": dict(sorted(class_counts.items())),
        "sample_class_quotas": dict(sorted(quotas.items())),
        "minimum_per_class": minimum_per_class,
        "random_seed": seed,
        "chunk_size": chunk_size,
        "note": (
            "This is a stratified training sample, not the complete archive. "
            "Run preprocessing on this sample to create an internal train/validation/test split. "
            "Full-archive evaluation is deferred."
        ),
    }
    metadata_path = output_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "data/raw/cicids2017_full")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/cicids2017_sample/raw/training_sample.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config/preprocessing.yaml",
    )
    parser.add_argument("--rows", type=int, default=71429)
    parser.add_argument("--minimum-per-class", type=int, default=500)
    parser.add_argument("--chunk-size", type=int, default=25000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = create_sample(
        input_dir=args.input,
        output_path=args.output,
        config_path=args.config,
        sample_size=args.rows,
        minimum_per_class=args.minimum_per_class,
        chunk_size=args.chunk_size,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
