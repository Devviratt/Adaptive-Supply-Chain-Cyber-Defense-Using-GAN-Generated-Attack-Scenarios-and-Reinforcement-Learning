"""
Integration tests for ASCCD Reinforcement Learning Pipeline (Phase 7).

Verifies the end-to-end integration:
Scenario Mapping -> Supply Chain Gym Env -> DQN Agent Training -> Policy Evaluation
and direct comparability with the Rule-Based Baseline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.baselines import RuleBasedDefensePolicy
from src.environment import SupplyChainEnv
from src.rl import DQNDefenseAgent
from src.scenarios.mapper import ScenarioMapper


class TestRLPipelineIntegration:
    """End-to-end integration test suite for RL defense pipeline."""

    def test_full_rl_training_and_comparison_pipeline(self) -> None:
        """Verify scenario generation, environment binding, rapid training, and baseline comparison."""
        # 1. Generate synthetic scenario batch
        mapper = ScenarioMapper()
        dummy_flow = {
            "Total Fwd Packets": 500,
            "Total Backward Packets": 200,
            "Flow Duration": 120_000,
            "SYN Flag Count": 15,
            "RST Flag Count": 2,
            "Label": "DDoS",
        }
        scenarios = mapper.map_batch([dummy_flow] * 5)
        assert len(scenarios) == 5

        # 2. Bind scenarios to SupplyChainEnv
        env = SupplyChainEnv(scenarios=scenarios)
        obs, info = env.reset(seed=42)
        assert len(obs) == 12

        # 3. Train DQN Agent in isolated temp directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent = DQNDefenseAgent(
                env=env,
                learning_starts=10,
                buffer_size=500,
                batch_size=16,
                n_eval_episodes=2,
                checkpoint_dir=tmp_dir,
            )

            train_result = agent.train(
                env=env,
                total_timesteps=40,
                condition="integration_test",
                save_checkpoints=False,
            )
            assert Path(train_result.model_path).exists()

            # 4. Evaluate DQN Agent
            dqn_eval = agent.evaluate(env, n_episodes=3, seed=100)
            assert dqn_eval.n_episodes == 3
            assert 0.0 <= dqn_eval.mitigation_rate <= 1.0

            # 5. Evaluate Rule-Based Baseline on identical environment
            baseline = RuleBasedDefensePolicy()
            base_eval = baseline.evaluate(env, n_episodes=3, seed=100)
            assert base_eval.n_episodes == 3
            assert 0.0 <= base_eval.mitigation_rate <= 1.0

            # 6. Verify identical interface outputs
            assert type(dqn_eval.mean_reward) is float
            assert type(base_eval.mean_reward) is float
            assert set(dqn_eval.action_distribution.keys()) == set(base_eval.action_distribution.keys())

        env.close()
