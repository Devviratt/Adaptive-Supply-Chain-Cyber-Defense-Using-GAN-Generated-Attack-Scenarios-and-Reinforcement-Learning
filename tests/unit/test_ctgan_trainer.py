"""
Unit tests for CTGAN trainer.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.gan.trainer import CTGANTrainer


@pytest.fixture
def sample_training_df() -> pd.DataFrame:
    """Provide a minimal clean training dataset for fast CTGAN testing."""
    np.random.seed(42)
    rows = 40
    data = {
        "Flow Duration": np.random.uniform(10.0, 1000.0, rows),
        "Total Fwd Packets": np.random.randint(1, 50, rows).astype(float),
        "Total Backward Packets": np.random.randint(1, 50, rows).astype(float),
        "Flow Bytes/s": np.random.uniform(100.0, 5000.0, rows),
        "Label": (["benign"] * 24 + ["dos"] * 10 + ["portscan"] * 6),
    }
    return pd.DataFrame(data)


def test_trainer_initialization_defaults():
    """Verify trainer initializes with expected defaults."""
    trainer = CTGANTrainer(seed=123)
    assert trainer.seed == 123
    assert trainer.batch_size % 2 == 0
    assert trainer.model is None
    assert trainer.report is None


def test_trainer_rejects_empty_data():
    """Verify trainer raises ValueError on empty DataFrame."""
    trainer = CTGANTrainer()
    with pytest.raises(ValueError, match="cannot be empty"):
        trainer.fit(pd.DataFrame())


def test_trainer_rejects_nan_and_inf(sample_training_df: pd.DataFrame):
    """Verify trainer strictly rejects data containing NaN or Inf."""
    trainer = CTGANTrainer()

    # Test with NaN
    df_nan = sample_training_df.copy()
    df_nan.iloc[0, 0] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        trainer.fit(df_nan)

    # Test with Inf
    df_inf = sample_training_df.copy()
    df_inf.iloc[0, 0] = np.inf
    with pytest.raises(ValueError, match="Infinite"):
        trainer.fit(df_inf)


def test_trainer_rejects_invalid_discrete_columns(sample_training_df: pd.DataFrame):
    """Verify trainer raises ValueError if configured discrete column is missing."""
    trainer = CTGANTrainer()
    with pytest.raises(ValueError, match="Discrete columns not found"):
        trainer.fit(sample_training_df, discrete_columns=["NonExistentColumn"])


def test_trainer_fit_and_save_load(sample_training_df: pd.DataFrame):
    """Verify CTGAN training loop, model serialization, and deserialization."""
    trainer = CTGANTrainer(epochs=2, batch_size=10, pac=1, seed=42)
    trainer.fit(sample_training_df, discrete_columns=["Label"])

    assert trainer.model is not None
    assert trainer.report is not None
    assert trainer.report.num_samples_trained == len(sample_training_df)
    assert "benign" in trainer.report.classes_present
    assert "dos" in trainer.report.classes_present

    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "ctgan_test.pkl"
        meta_file = Path(tmpdir) / "ctgan_test.json"

        trainer.save(model_file, meta_file)
        assert model_file.exists()
        assert meta_file.exists()

        # Load back
        loaded_trainer = CTGANTrainer.load(model_file, meta_file)
        assert loaded_trainer.model is not None
        assert loaded_trainer.report is not None
        assert loaded_trainer.report.num_samples_trained == len(sample_training_df)
