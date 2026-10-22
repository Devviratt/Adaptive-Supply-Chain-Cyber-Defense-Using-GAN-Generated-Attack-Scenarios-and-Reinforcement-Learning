"""
Unit tests for ASCCD PPO Defense Agent (Phase 7 - Comparison Agent).
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import gymnasium as gym
import numpy as np
import pytest

from src.rl import PPODefenseAgent, PPOEvaluationResult, PPOTrainingResult


class TestPPODefenseAgent:
    """Unit test suite for the Proximal Policy Optimization reinforcement learning agent."""

    @pytest.fixture
    def env(self) -> gym.Env:
        """Create fresh SupplyChainEnv instance."""
        env = gym.make("asccd/SupplyChain-v0")
        yield env
        env.close()

    @pytest.fixture
    def agent(self, env: gym.Env) -> PPODefenseAgent:
        """Create fast-testing PPO agent."""
        return PPODefenseAgent(
            env=env,
            n_steps=32,
            batch_size=16,
            n_epochs=2,
            n_eval_episodes=2,
            save_freq=0,
        )

    def test_agent_initialization(self, agent: PPODefenseAgent) -> None:
        """Verify agent hyperparameter initialization."""
        assert agent.algorithm == "PPO"
        assert agent.policy_name == "MlpPolicy"
        assert agent.n_steps == 32
        assert agent.batch_size == 16
        assert agent.model is not None

    def test_get_hyperparameters(self, agent: PPODefenseAgent) -> None:
        """Verify hyperparameters dictionary retrieval."""
        params = agent.get_hyperparameters()
        assert params["algorithm"] == "PPO"
        assert params["n_steps"] == 32
        assert "learning_rate" in params
        assert "clip_range" in params

    def test_predict_returns_valid_action(self, agent: PPODefenseAgent) -> None:
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
            agent = PPODefenseAgent(
                env=env,
                n_steps=32,
                batch_size=16,
                n_epochs=1,
                n_eval_episodes=2,
                checkpoint_dir=tmp_dir,
            )
            result = agent.train(
                env=env,
                total_timesteps=32,
                condition="test",
                save_checkpoints=False,
            )

            assert isinstance(result, PPOTrainingResult)
            assert result.total_timesteps == 32
            assert result.condition == "test"
            assert result.training_duration_seconds > 0.0
            assert Path(result.model_path).exists()

    def test_evaluate_produces_valid_metrics(self, agent: PPODefenseAgent, env: gym.Env) -> None:
        """Verify evaluation over episodes produces sound metrics dataclass."""
        eval_res = agent.evaluate(env, n_episodes=3, seed=123)

        assert isinstance(eval_res, PPOEvaluationResult)
        assert eval_res.n_episodes == 3
        assert isinstance(eval_res.mean_reward, float)
        assert 0.0 <= eval_res.mitigation_rate <= 1.0
        assert 0.0 <= eval_res.mean_availability <= 1.0
        assert eval_res.mean_episode_length > 0
        assert len(eval_res.episode_rewards) == 3
        assert sum(eval_res.action_distribution.values()) > 0

    def test_save_and_load(self, agent: PPODefenseAgent, env: gym.Env) -> None:
        """Verify model weights serialization and deserialization."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "test_ppo_model.zip"
            saved_file = agent.save(save_path)
            assert saved_file.exists()

            loaded_agent = PPODefenseAgent.load(saved_file, env=env)
            assert loaded_agent.model is not None

            test_obs = np.ones(12, dtype=np.float32) * 0.5
            action_orig, _ = agent.predict(test_obs, deterministic=True)
            action_loaded, _ = loaded_agent.predict(test_obs, deterministic=True)
            assert action_orig == action_loaded

    def test_result_to_dict_serialization(self) -> None:
        """Verify PPOTrainingResult and PPOEvaluationResult to_dict converters."""
        t_res = PPOTrainingResult(
            model_path="models/ppo_test.zip",
            total_timesteps=5000,
            training_duration_seconds=8.5,
            condition="augmented",
            checkpoints=["ckpt.zip"],
            final_eval_reward=35.2,
            mitigation_rate=0.75,
        )
        d_t = t_res.to_dict()
        assert d_t["total_timesteps"] == 5000
        assert d_t["condition"] == "augmented"
        assert d_t["mitigation_rate"] == 0.75

        e_res = PPOEvaluationResult(
            model_name="ppo_agent",
            n_episodes=5,
            mean_reward=72.0,
            std_reward=5.1,
            mitigation_rate=0.80,
            mean_availability=0.96,
            mean_episode_length=11.2,
            mitigated_episodes=4,
            catastrophic_failures=0,
        )
        d_e = e_res.to_dict()
        assert d_e["model_name"] == "ppo_agent"
        assert d_e["mean_reward"] == 72.0
        assert d_e["mitigation_rate"] == 0.80
