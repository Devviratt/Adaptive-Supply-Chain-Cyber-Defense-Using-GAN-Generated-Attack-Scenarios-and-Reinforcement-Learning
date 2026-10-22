"""
Integration tests for ASCCD Evaluation Pipeline (Phase 8).

Verifies the full evaluation flow:
Controlled Multi-Experiment Execution -> Metrics Aggregation -> Relative Gains -> Database Logging -> Report Export
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from src.common.models import Experiment
from src.evaluation import ComparisonSummary, EvaluationEngine


class TestEvaluationPipelineIntegration:
    """Integration test suite for the evaluation pipeline."""

    def test_full_evaluation_pipeline_with_database(self, db_session) -> None:
        """Verify multi-condition benchmarking, database insertion, and report generation."""
        engine = EvaluationEngine()

        # Run experiments A and B in accelerated mode
        summary = engine.run_all_experiments(
            experiment_ids=["A", "B"],
            n_episodes=2,
            dev_mode=True,
            session=db_session,
        )

        assert isinstance(summary, ComparisonSummary)
        assert "A" in summary.experiments
        assert "B" in summary.experiments

        # Verify database persistence
        exp_a_db = db_session.query(Experiment).filter_by(experiment_id="exp_a").first()
        assert exp_a_db is not None
        assert exp_a_db.status == "completed"

        exp_b_db = db_session.query(Experiment).filter_by(experiment_id="exp_b").first()
        assert exp_b_db is not None
        assert exp_b_db.status == "completed"

        # Verify report generation
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_p, csv_p, fig_p = engine.export_reports(summary, output_dir=tmp_dir)
            assert json_p.exists()
            assert csv_p.exists()
