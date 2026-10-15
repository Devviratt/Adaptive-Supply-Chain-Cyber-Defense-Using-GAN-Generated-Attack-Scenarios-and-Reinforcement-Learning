"""
Unit tests for synthetic data validator.
"""

from __future__ import annotations

import tempfile

import numpy as np
import pandas as pd
import pytest
from src.gan.validator import SyntheticDataValidator, ValidationThresholds


@pytest.fixture
def baseline_dfs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Provide realistic matching real and synthetic DataFrames."""
    np.random.seed(42)
    n = 100
    real = pd.DataFrame(
        {
            "Flow Duration": np.random.exponential(scale=50.0, size=n),
            "Total Fwd Packets": np.random.poisson(lam=10, size=n).astype(float),
            "Flow Bytes/s": np.random.normal(loc=1000.0, scale=200.0, size=n),
            "Label": (["benign"] * 60 + ["dos"] * 30 + ["ddos"] * 10),
        }
    )

    # Synthetic with slight variance from real
    synth = pd.DataFrame(
        {
            "Flow Duration": np.random.exponential(scale=52.0, size=n),
            "Total Fwd Packets": np.random.poisson(lam=10.2, size=n).astype(float),
            "Flow Bytes/s": np.random.normal(loc=1010.0, scale=205.0, size=n),
            "Label": (["benign"] * 60 + ["dos"] * 30 + ["ddos"] * 10),
        }
    )
    return real, synth


def test_validator_passes_on_similar_data(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator passes when synthetic data matches real distribution closely."""
    real, synth = baseline_dfs
    validator = SyntheticDataValidator()
    summary = validator.validate(real, synth)

    assert summary.schema_passed is True
    assert summary.no_nan_or_inf_passed is True
    assert summary.valid_labels_passed is True
    assert summary.mean_wasserstein_distance < 0.20
    assert summary.mean_js_divergence < 0.35
    assert summary.correlation_similarity > 0.70


def test_validator_fails_on_column_mismatch(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator flags missing or altered columns."""
    real, synth = baseline_dfs
    synth_bad = synth.drop(columns=["Flow Duration"])

    validator = SyntheticDataValidator()
    summary = validator.validate(real, synth_bad)

    assert summary.schema_passed is False
    assert any("missing columns" in r for r in summary.failure_reasons)


def test_validator_fails_on_nan_inf(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator flags presence of NaN or Inf values."""
    real, synth = baseline_dfs
    synth_nan = synth.copy()
    synth_nan.iloc[0, 0] = np.nan

    validator = SyntheticDataValidator()
    summary = validator.validate(real, synth_nan)

    assert summary.no_nan_or_inf_passed is False
    assert any("non-finite" in r for r in summary.failure_reasons)


def test_validator_fails_on_invented_labels(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator flags hallucinated classes not in training."""
    real, synth = baseline_dfs
    synth_invented = synth.copy()
    synth_invented.iloc[0, synth.columns.get_loc("Label")] = "hallucinated_exploit"

    validator = SyntheticDataValidator()
    summary = validator.validate(real, synth_invented)

    assert summary.valid_labels_passed is False
    assert any("invented labels" in r for r in summary.failure_reasons)


def test_validator_detects_excessive_duplicates(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator catches severe duplicate ratio in synthetic data."""
    real, _ = baseline_dfs
    # Create duplicate-heavy synthetic data (all identical rows)
    synth_dups = pd.concat([real.iloc[[0]]] * 100, ignore_index=True)

    thresholds = ValidationThresholds(max_duplicate_ratio=0.05)
    validator = SyntheticDataValidator(thresholds=thresholds)
    summary = validator.validate(real, synth_dups)

    assert summary.synthetic_duplicate_ratio > 0.90
    assert any("duplicate ratio" in r for r in summary.failure_reasons)


def test_validator_detects_mode_collapse(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify validator detects zero-variance mode-collapsed features."""
    real, synth = baseline_dfs
    synth_collapsed = synth.copy()
    synth_collapsed["Flow Duration"] = 50.0  # Constant value (0 variance)

    thresholds = ValidationThresholds(max_mode_collapsed_features=0)
    validator = SyntheticDataValidator(thresholds=thresholds)
    summary = validator.validate(real, synth_collapsed)

    assert "Flow Duration" in summary.mode_collapsed_features
    assert any("mode-collapsed" in r for r in summary.failure_reasons)


def test_validator_export_reports(baseline_dfs: tuple[pd.DataFrame, pd.DataFrame]):
    """Verify export_reports generates valid JSON and Markdown files."""
    real, synth = baseline_dfs
    validator = SyntheticDataValidator()
    summary = validator.validate(real, synth)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_p, md_p = validator.export_reports(summary, tmpdir)
        assert json_p.exists()
        assert md_p.exists()
        assert md_p.stat().st_size > 100
