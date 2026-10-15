"""
Integration tests for the complete CTGAN synthetic data pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from src.gan.evaluation import DownstreamUtilityEvaluator
from src.gan.generator import SyntheticAttackGenerator
from src.gan.trainer import CTGANTrainer
from src.gan.validator import SyntheticDataValidator


def test_end_to_end_gan_pipeline():
    """Verify complete Phase 3 pipeline: Train CTGAN -> Generate -> Validate -> Evaluate."""
    np.random.seed(42)

    # 1. Realistic feature matrix
    cols = [f"feat_{i}" for i in range(10)]
    n_train = 60
    n_test = 20

    train_data = {c: np.random.uniform(0, 100, n_train) for c in cols}
    train_data["Label"] = ["benign"] * 40 + ["dos"] * 12 + ["portscan"] * 8
    train_df = pd.DataFrame(train_data)

    test_data = {c: np.random.uniform(0, 100, n_test) for c in cols}
    test_data["Label"] = ["benign"] * 14 + ["dos"] * 4 + ["portscan"] * 2
    test_df = pd.DataFrame(test_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        model_path = tmp_path / "model.pkl"
        meta_path = tmp_path / "meta.json"
        synth_path = tmp_path / "synthetic.csv"
        reports_dir = tmp_path / "reports"

        # 2. Train CTGAN
        trainer = CTGANTrainer(epochs=2, batch_size=10, pac=1, seed=42)
        trainer.fit(train_df, discrete_columns=["Label"])
        trainer.save(model_path, meta_path)

        assert model_path.exists()
        assert meta_path.exists()

        # 3. Generate Synthetic Attacks
        generator = SyntheticAttackGenerator.from_checkpoint(model_path, meta_path)
        synth_df = generator.generate_conditional({"dos": 8, "portscan": 8}, seed=42)

        generator.save_synthetic_data(synth_df, synth_path)
        assert synth_path.exists()
        assert len(synth_df) > 0
        assert set(synth_df.columns) == set(train_df.columns)

        # 4. Validate Synthetic Data
        validator = SyntheticDataValidator()
        summary = validator.validate(train_df, synth_df)
        json_p, md_p = validator.export_reports(summary, reports_dir)

        assert json_p.exists()
        assert md_p.exists()
        assert summary.schema_passed is True
        assert summary.no_nan_or_inf_passed is True

        # 5. Downstream Utility Evaluation
        evaluator = DownstreamUtilityEvaluator(random_state=42, n_estimators=10)
        util_report = evaluator.evaluate_utility(train_df, synth_df, test_df)
        u_json, u_md = evaluator.export_reports(util_report, reports_dir)

        assert u_json.exists()
        assert u_md.exists()
        assert util_report.test_sample_count == len(test_df)
        assert isinstance(util_report.macro_f1_delta, float)
