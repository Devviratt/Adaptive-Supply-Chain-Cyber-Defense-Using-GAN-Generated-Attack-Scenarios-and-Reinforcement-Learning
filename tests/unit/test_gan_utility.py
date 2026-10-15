"""
Unit tests for downstream ML utility evaluation.
"""

from __future__ import annotations

import tempfile

import numpy as np
import pandas as pd
import pytest
from src.gan.evaluation import DownstreamUtilityEvaluator


@pytest.fixture
def utility_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Provide minimal real train, synthetic train, and real test sets."""
    np.random.seed(42)

    def make_partition(n: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "feat1": np.random.normal(0, 1, n),
                "feat2": np.random.normal(5, 2, n),
                "Label": ["benign"] * int(n * 0.7) + ["dos"] * int(n * 0.3),
            }
        )

    train_real = make_partition(100)
    synthetic = make_partition(50)
    test_real = make_partition(40)
    return train_real, synthetic, test_real


def test_utility_evaluator_runs_and_produces_metrics(
    utility_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
):
    """Verify evaluator trains both models, scores on test set, and calculates deltas."""
    train_real, synthetic, test_real = utility_data
    evaluator = DownstreamUtilityEvaluator(random_state=42, n_estimators=10)
    report = evaluator.evaluate_utility(train_real, synthetic, test_real)

    assert report.test_sample_count == len(test_real)
    assert report.model_a_real_only.accuracy > 0.50
    assert report.model_b_augmented.accuracy > 0.50
    assert "dos" in report.minority_class_f1_improvements
    assert isinstance(report.macro_f1_delta, float)


def test_utility_evaluator_missing_label_raises(
    utility_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
):
    """Verify evaluator raises ValueError if label column is absent."""
    train_real, synthetic, test_real = utility_data
    evaluator = DownstreamUtilityEvaluator(random_state=42, n_estimators=10)

    with pytest.raises(ValueError, match="not found"):
        evaluator.evaluate_utility(train_real.drop(columns=["Label"]), synthetic, test_real)


def test_utility_evaluator_export_reports(
    utility_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
):
    """Verify report export produces JSON and Markdown reports."""
    train_real, synthetic, test_real = utility_data
    evaluator = DownstreamUtilityEvaluator(random_state=42, n_estimators=10)
    report = evaluator.evaluate_utility(train_real, synthetic, test_real)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_p, md_p = evaluator.export_reports(report, tmpdir)
        assert json_p.exists()
        assert md_p.exists()
        assert md_p.stat().st_size > 100
