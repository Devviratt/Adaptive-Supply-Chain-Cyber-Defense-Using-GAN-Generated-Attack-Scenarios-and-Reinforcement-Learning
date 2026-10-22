"""
Unit tests for ASCCD Evaluation Engine (Phase 8).
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import gymnasium as gym
import pytest

from src.baselines import RuleBasedDefensePolicy
from src.evaluation import ComparisonSummary, EvaluationEngine, ExperimentResult


class TestEvaluationEngine:
    """Unit test suite for the scientific evaluation engine."""

    @pytest.fixture
    def engine(self) -> EvaluationEngine:
        """Create fresh EvaluationEngine instance."""
        return EvaluationEngine()

    @pytest.fixture
    def env(self) -> gym.Env:
        """Create fresh SupplyChainEnv instance."""
        env = gym.make("asccd/SupplyChain-v0")
        yield env
        env.close()

    def test_engine_initialization(self, engine: EvaluationEngine) -> None:
        """Verify engine initialization and config loading."""
        assert "A" in engine.experiments_cfg
        assert "B" in engine.experiments_cfg
        assert "C" in engine.experiments_cfg
        assert len(engine.seeds) > 0

    def test_evaluate_policy_metrics(self, engine: EvaluationEngine, env: gym.Env) -> None:
        """Verify comprehensive metrics computed during policy evaluation."""
        policy = RuleBasedDefensePolicy()
        result = engine.evaluate_policy(
            policy=policy,
            env=env,
            experiment_id="A",
            name="Rule-Based Baseline",
            model_type="rule_based",
            dataset="real",
            n_episodes=3,
            seeds=[42, 100],
        )

        assert isinstance(result, ExperimentResult)
        assert result.experiment_id == "A"
        assert result.n_episodes == 3
        assert 0.0 <= result.mitigation_success_rate <= 1.0
        assert 0.0 <= result.containment_rate <= 1.0
        assert 0.0 <= result.service_availability <= 1.0
        assert isinstance(result.mean_reward, float)
        assert isinstance(result.attack_impact_score, float)
        assert len(result.episode_rewards) == 3
        assert isinstance(result.performance_by_attack_class, dict)

    def test_run_experiment_A(self, engine: EvaluationEngine) -> None:
        """Verify execution of Experiment A."""
        result = engine.run_experiment("A", n_episodes=2, dev_mode=True)
        assert result.experiment_id == "A"
        assert result.model_type == "rule_based"
        assert result.n_episodes == 2

    def test_comparison_summary_serialization(self) -> None:
        """Verify ComparisonSummary serialization and gain calculations."""
        res_a = ExperimentResult(
            experiment_id="A",
            name="Baseline",
            model_type="rule_based",
            dataset="real",
            n_episodes=10,
            mitigation_success_rate=0.50,
            service_availability=0.95,
            mean_reward=50.0,
        )
        res_c = ExperimentResult(
            experiment_id="C",
            name="DQN+GAN",
            model_type="dqn_gan",
            dataset="real+synthetic",
            n_episodes=10,
            mitigation_success_rate=0.85,
            service_availability=0.99,
            mean_reward=80.0,
        )

        summary = ComparisonSummary(
            experiments={"A": res_a, "C": res_c},
            relative_gains={
                "C_vs_A": {
                    "mitigation_delta_pct": 35.0,
                    "reward_delta": 30.0,
                }
            },
            timestamp="2026-10-22T16:00:00Z",
        )
        d = summary.to_dict()
        assert "experiments" in d
        assert "relative_gains" in d
        assert d["relative_gains"]["C_vs_A"]["mitigation_delta_pct"] == 35.0

    def test_export_reports(self, engine: EvaluationEngine) -> None:
        """Verify JSON, CSV, and plot file generation."""
        res_a = ExperimentResult(
            experiment_id="A",
            name="Baseline",
            model_type="rule_based",
            dataset="real",
            n_episodes=5,
            mitigation_success_rate=0.60,
            service_availability=0.96,
            mean_reward=45.0,
            std_reward=5.0,
        )
        summary = ComparisonSummary(
            experiments={"A": res_a},
            relative_gains={},
            timestamp="2026-10-22T16:00:00Z",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            json_p, csv_p, fig_p = engine.export_reports(summary, output_dir=tmp_dir)
            assert json_p.exists()
            assert csv_p.exists()
            assert json_p.suffix == ".json"
            assert csv_p.suffix == ".csv"
