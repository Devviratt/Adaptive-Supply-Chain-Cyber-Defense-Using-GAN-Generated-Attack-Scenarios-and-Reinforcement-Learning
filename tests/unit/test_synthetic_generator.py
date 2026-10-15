"""
Unit tests for synthetic attack generator.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.gan.generator import SyntheticAttackGenerator
from src.gan.trainer import CTGANTrainer


@pytest.fixture
def trained_trainer() -> CTGANTrainer:
    """Fixture providing a fast-trained CTGANTrainer."""
    np.random.seed(42)
    rows = 40
    data = {
        "Flow Duration": np.random.uniform(10.0, 500.0, rows),
        "Total Fwd Packets": np.random.randint(1, 20, rows).astype(float),
        "Label": (["benign"] * 24 + ["dos"] * 10 + ["portscan"] * 6),
    }
    df = pd.DataFrame(data)
    trainer = CTGANTrainer(epochs=2, batch_size=10, pac=1, seed=42)
    trainer.fit(df, discrete_columns=["Label"])
    return trainer


def test_generator_initialization_validation():
    """Verify generator validates presence of model or trainer."""
    with pytest.raises(ValueError, match="Either 'trainer' or 'model' must be provided"):
        SyntheticAttackGenerator()


def test_generator_unconditional_sampling(trained_trainer: CTGANTrainer):
    """Verify unconditional sampling generates expected sample count and columns."""
    gen = SyntheticAttackGenerator(trainer=trained_trainer)
    synth_df = gen.generate(num_samples=15, seed=42)

    assert len(synth_df) == 15
    assert list(synth_df.columns) == trained_trainer._feature_names
    assert not synth_df.isnull().any().any()
    assert np.isfinite(synth_df.select_dtypes(include=[np.number]).values).all()


def test_generator_conditional_sampling_known_classes(trained_trainer: CTGANTrainer):
    """Verify conditional generation produces targeted attack samples."""
    gen = SyntheticAttackGenerator(trainer=trained_trainer)
    targets = {"dos": 5, "portscan": 5}
    synth_df = gen.generate_conditional(targets, seed=42)

    assert len(synth_df) > 0
    assert "Label" in synth_df.columns
    assert set(synth_df["Label"].unique()).issubset({"dos", "portscan"})


def test_generator_rejects_absent_classes(trained_trainer: CTGANTrainer):
    """Verify generator refuses to fabricate samples for classes not seen during training."""
    gen = SyntheticAttackGenerator(trainer=trained_trainer)
    with pytest.raises(ValueError, match="not present in training data"):
        gen.generate_conditional({"infiltration": 10})


def test_generator_clamping_and_non_finite_handling(trained_trainer: CTGANTrainer):
    """Verify generator cleans non-finites and clamps negative physical metrics."""
    gen = SyntheticAttackGenerator(trainer=trained_trainer)
    raw_df = pd.DataFrame(
        {
            "Flow Duration": [-50.0, 100.0, np.nan, np.inf],
            "Total Fwd Packets": [5.0, -2.0, 10.0, 20.0],
            "Label": ["benign", "dos", "dos", "benign"],
        }
    )

    cleaned, meta = gen._postprocess_and_clean(raw_df, mode="test", seed=42)
    assert not cleaned.isnull().any().any()
    assert np.isfinite(cleaned[["Flow Duration", "Total Fwd Packets"]].values).all()
    assert (cleaned["Flow Duration"] >= 0).all()
    assert (cleaned["Total Fwd Packets"] >= 0).all()
    assert meta.clamped_features_count > 0


def test_generator_save_synthetic_data(trained_trainer: CTGANTrainer):
    """Verify saving synthetic data creates CSV and metadata JSON."""
    gen = SyntheticAttackGenerator(trainer=trained_trainer)
    df = gen.generate(10, seed=42)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_csv = Path(tmpdir) / "synthetic.csv"
        gen.save_synthetic_data(df, out_csv)

        assert out_csv.exists()
        assert out_csv.with_suffix(".metadata.json").exists()
