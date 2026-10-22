"""
Unit tests for ASCCD DQN Defense Agent (Phase 7).
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import gymnasium as gym
import numpy as np
import pytest

from src.environment import DefenseAction
from src.rl import DQNDefenseAgent, DQNEvaluationResult, DQNTrainingResult


class TestDQNDefenseAgent:
    """Unit test suite for the Deep Q-Network reinforcement learning agent."""

    @pytest.fixture
    def env(self) -> gym.Env:
        """Create fresh SupplyChainEnv instance."""
        env = gym.make("asccd/SupplyChain-v0")
        yield env
        env.close()

    @pytest.fixture
    def agent(self, env: gym.Env) -> DQNDefenseAgent:
        """Create fast-testing DQN agent."""
        return DQNDefenseAgent(
            env=env,
            learning_starts=10,
            buffer_size=1000,
            batch_size=16,
            n_eval_episodes=2,
            save_freq=0,
        )

    def test_agent_initialization(self, agent: DQNDefenseAgent) -> None:
        """Verify agent hyperparameter initialization."""
        assert agent.algorithm == "DQN"
        assert agent.policy_name == "MlpPolicy"
        assert agent.learning_starts == 10
        assert agent.buffer_size == 1000
        assert agent.model is not None

    def test_get_hyperparameters(self, agent: DQNDefenseAgent) -> None:
        """Verify hyperparameters dictionary retrieval."""
        params = agent.get_hyperparameters()
        assert params["algorithm"] == "DQN"
        assert params["buffer_size"] == 1000
        assert params["learning_starts"] == 10
        assert "learning_rate" in params

    def test_predict_returns_valid_action(self, agent: DQNDefenseAgent) -> None:
        """Verify action prediction output type and valid discrete action range."""
        sample_obs = np.array(
            [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.2, 0.1],
            dtype=np.float32,
        )
        action, state = agent.predict(sample_obs)
        assert isinstance(action, int)
        assert 0 <= action <= 4
        assert state is None

    def test_train_abbreviated_cycle(self, env: gym.Env) -> None:
        """Verify rapid training cycle completes and produces valid training result."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent = DQNDefenseAgent(
                env=env,
                learning_starts=10,
                buffer_size=500,
                batch_size=16,
                n_eval_episodes=2,
                checkpoint_dir=tmp_dir,
            )
            result = agent.train(
                env=env,
                total_timesteps=30,
                condition="test",
                save_checkpoints=False,
            )

            assert isinstance(result, DQNTrainingResult)
            assert result.total_timesteps == 30
            assert result.condition == "test"
            assert result.training_duration_seconds > 0.0
            assert Path(result.model_path).exists()

    def test_evaluate_produces_valid_metrics(self, agent: DQNDefenseAgent, env: gym.Env) -> None:
        """Verify evaluation over episodes produces sound metrics dataclass."""
        eval_res = agent.evaluate(env, n_episodes=3, seed=123)

        assert isinstance(eval_res, DQNEvaluationResult)
        assert eval_res.n_episodes == 3
        assert isinstance(eval_res.mean_reward, float)
        assert 0.0 <= eval_res.mitigation_rate <= 1.0
        assert 0.0 <= eval_res.mean_availability <= 1.0
        assert eval_res.mean_episode_length > 0
        assert len(eval_res.episode_rewards) == 3
        assert sum(eval_res.action_distribution.values()) > 0

    def test_save_and_load(self, agent: DQNDefenseAgent, env: gym.Env) -> None:
        """Verify model weights serialization and deserialization."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "test_dqn_model.zip"
            saved_file = agent.save(save_path)
            assert saved_file.exists()

            # Deserialization via classmethod
            loaded_agent = DQNDefenseAgent.load(saved_file, env=env)
            assert loaded_agent.model is not None

            # Verify predictions work identically
            test_obs = np.ones(12, dtype=np.float32) * 0.5
            action_orig, _ = agent.predict(test_obs, deterministic=True)
            action_loaded, _ = loaded_agent.predict(test_obs, deterministic=True)
            assert action_orig == action_loaded

    def test_result_to_dict_serialization(self) -> None:
        """Verify DQNTrainingResult and DQNEvaluationResult to_dict converters."""
        t_res = DQNTrainingResult(
            model_path="models/test.zip",
            total_timesteps=1000,
            training_duration_seconds=12.345,
            condition="real_only",
            checkpoints=["ckpt1.zip"],
            final_eval_reward=45.67,
            mitigation_rate=0.85,
        )
        d_t = t_res.to_dict()
        assert d_t["total_timesteps"] == 1000
        assert d_t["condition"] == "real_only"
        assert d_t["mitigation_rate"] == 0.85

        e_res = DQNEvaluationResult(
            model_name="dqn_agent",
            n_episodes=10,
            mean_reward=88.5,
            std_reward=10.2,
            mitigation_rate=0.90,
            mean_availability=0.98,
            mean_episode_length=8.5,
            mitigated_episodes=9,
            catastrophic_failures=0,
        )
        d_e = e_res.to_dict()
        assert d_e["model_name"] == "dqn_agent"
        assert d_e["mean_reward"] == 88.5
        assert d_e["mitigation_rate"] == 0.90
