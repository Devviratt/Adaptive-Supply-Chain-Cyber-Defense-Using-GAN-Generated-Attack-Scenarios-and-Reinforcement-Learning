"""CTGAN training, sampling, and lightweight fidelity checks for processed tabular data."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def train_ctgan(
    train_path: str | Path,
    model_path: str | Path,
    config: dict[str, Any],
    label_column: str = "Label",
) -> dict[str, Any]:
    """Fit CTGAN using only the supplied training split and persist the synthesizer."""
    from ctgan import CTGAN

    data = pd.read_csv(train_path)
    if data.empty:
        raise ValueError(f"Training data is empty: {train_path}")
    if label_column not in data.columns:
        raise ValueError(f"Expected discrete label column {label_column!r} in {train_path}")
    data[label_column] = data[label_column].astype(str)
    ctgan_cfg = config.get("ctgan", config)
    seed = int(ctgan_cfg.get("seed", 42))
    np.random.seed(seed)
    ctgan_options = dict(
        epochs=int(ctgan_cfg.get("epochs", 50)),
        batch_size=int(ctgan_cfg.get("batch_size", 500)),
        generator_dim=tuple(ctgan_cfg.get("generator_dim", [256, 256])),
        discriminator_dim=tuple(ctgan_cfg.get("discriminator_dim", [256, 256])),
        generator_lr=float(ctgan_cfg.get("generator_lr", 2e-4)),
        discriminator_lr=float(ctgan_cfg.get("discriminator_lr", 2e-4)),
        discriminator_steps=int(ctgan_cfg.get("discriminator_steps", 1)),
        verbose=bool(ctgan_cfg.get("verbose", True)),
    )
    # CTGAN 0.12 renamed ``cuda`` to ``enable_gpu``.
    if "enable_gpu" in inspect.signature(CTGAN).parameters:
        ctgan_options["enable_gpu"] = False
    else:
        ctgan_options["cuda"] = False
    model = CTGAN(**ctgan_options)
    model.fit(data, discrete_columns=[label_column])
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))
    metadata = {
        "model": str(model_path),
        "training_data": str(train_path),
        "training_rows": len(data),
        "columns": list(data.columns),
        "discrete_columns": [label_column],
        "seed": seed,
        "epochs": int(ctgan_cfg.get("epochs", 50)),
    }
    model_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def generate_ctgan(
    model_path: str | Path,
    output_path: str | Path,
    count: int,
    seed: int = 42,
    class_column: str = "Label",
    per_class: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Generate samples, optionally requesting counts for specific label values."""
    from ctgan import CTGAN

    if count < 1:
        raise ValueError("count must be positive")
    np.random.seed(seed)
    model = CTGAN.load(str(model_path))
    frames: list[pd.DataFrame] = []
    if per_class:
        for label, amount in per_class.items():
            if int(amount) < 1:
                continue
            frames.append(model.sample(int(amount), condition_column=class_column, condition_value=str(label)))
        generated = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    else:
        generated = model.sample(count)
    if generated.empty:
        raise ValueError("No rows generated; check requested per-class counts")
    generated["data_origin"] = "synthetic_ctgan"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated.to_csv(output_path, index=False)
    return generated


def validate_synthetic(
    real_path: str | Path,
    synthetic_path: str | Path,
    report_path: str | Path,
    label_column: str = "Label",
) -> dict[str, Any]:
    """Write basic schema, validity, diversity, label balance, and KS fidelity metrics."""
    real = pd.read_csv(real_path)
    synthetic = pd.read_csv(synthetic_path)
    synthetic = synthetic.drop(columns=["data_origin"], errors="ignore")
    real_cols, synth_cols = set(real.columns), set(synthetic.columns)
    common = [column for column in real.columns if column in synth_cols]
    numeric = [c for c in common if c != label_column and pd.api.types.is_numeric_dtype(real[c])]
    ks = {}
    for column in numeric:
        lhs = pd.to_numeric(real[column], errors="coerce").dropna()
        rhs = pd.to_numeric(synthetic[column], errors="coerce").dropna()
        if len(lhs) and len(rhs):
            ks[column] = float(ks_2samp(lhs, rhs).statistic)
    label_distribution = {}
    if label_column in synthetic:
        label_distribution = synthetic[label_column].astype(str).value_counts(normalize=True).round(6).to_dict()
    report = {
        "real_rows": len(real),
        "synthetic_rows": len(synthetic),
        "schema_matches": real_cols == synth_cols,
        "missing_columns": sorted(real_cols - synth_cols),
        "extra_columns": sorted(synth_cols - real_cols),
        "numeric_columns_checked": len(ks),
        "mean_ks_statistic": float(np.mean(list(ks.values()))) if ks else None,
        "max_ks_statistic": max(ks.values()) if ks else None,
        "duplicate_ratio": float(synthetic.duplicated().mean()) if len(synthetic) else 0.0,
        "non_finite_numeric_values": int(synthetic.select_dtypes(include=[np.number]).apply(lambda c: ~np.isfinite(c)).sum().sum()),
        "synthetic_label_distribution": label_distribution,
        "ks_statistic_by_feature": ks,
        "note": "Descriptive fidelity checks only; passing does not establish downstream utility or improve RL defense.",
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown = ["# CTGAN Synthetic Data Validation", "", f"- Real rows: {report['real_rows']}", f"- Synthetic rows: {report['synthetic_rows']}", f"- Schema matches: {report['schema_matches']}", f"- Mean numeric KS statistic: {report['mean_ks_statistic']}", f"- Duplicate ratio: {report['duplicate_ratio']:.4f}", f"- Non-finite numeric values: {report['non_finite_numeric_values']}", "", "Synthetic label proportions:"]
    markdown += [f"- {label}: {share:.4f}" for label, share in label_distribution.items()]
    markdown += ["", report["note"]]
    report_path.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return report
