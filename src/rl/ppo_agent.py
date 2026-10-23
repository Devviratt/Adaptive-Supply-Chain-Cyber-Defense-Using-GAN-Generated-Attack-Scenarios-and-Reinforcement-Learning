"""
ASCCD Proximal Policy Optimization (PPO) Defense Agent.

Implements the on-policy policy gradient reinforcement learning cyber-defense policy
using Stable-Baselines3. Serves as the comparative baseline agent (Experiment D)
against the primary Deep Q-Network (DQN) defense agent.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import structlog
import yaml
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

from src.environment.models import DefenseAction
from src.rl.models import PPOEvaluationResult, PPOTrainingResult

logger = structlog.get_logger(__name__)


class PPODefenseAgent:
    """Proximal Policy Optimization reinforcement learning agent for supply chain defense.

    Utilizes clipped surrogate objective actor-critic networks to learn defensive
    policies over discrete supply-chain action spaces.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
        env: gym.Env | None = None,
        model: PPO | None = None,
        **hyperparameter_overrides: Any,
    ) -> None:
        """Initialize the PPO defense agent.

        Args:
            config: Optional pre-loaded configuration dictionary.
            config_path: Optional path to YAML configuration file (default: config/ppo.yaml).
            env: Optional Gymnasium environment instance.
            model: Optional pre-existing Stable-Baselines3 PPO model.
            **hyperparameter_overrides: Explicit overrides for any configuration parameters.
        """
        self.config = self._load_config(config, config_path)
        ppo_cfg = self.config.get("ppo", {})

        # Algorithm & Policy
        self.algorithm = ppo_cfg.get("algorithm", "PPO")
        self.policy_name = ppo_cfg.get("policy", "MlpPolicy")

        # Hyperparameters
        self.learning_rate = float(
            hyperparameter_overrides.get("learning_rate", ppo_cfg.get("learning_rate", 3.0e-4))
        )
        self.n_steps = int(hyperparameter_overrides.get("n_steps", ppo_cfg.get("n_steps", 2048)))
        self.batch_size = int(
            hyperparameter_overrides.get("batch_size", ppo_cfg.get("batch_size", 64))
        )
        self.n_epochs = int(hyperparameter_overrides.get("n_epochs", ppo_cfg.get("n_epochs", 10)))
        self.gamma = float(hyperparameter_overrides.get("gamma", ppo_cfg.get("gamma", 0.99)))
        self.gae_lambda = float(
            hyperparameter_overrides.get("gae_lambda", ppo_cfg.get("gae_lambda", 0.95))
        )
        self.clip_range = float(
            hyperparameter_overrides.get("clip_range", ppo_cfg.get("clip_range", 0.2))
        )
        self.ent_coef = float(
            hyperparameter_overrides.get("ent_coef", ppo_cfg.get("ent_coef", 0.01))
        )
        self.vf_coef = float(hyperparameter_overrides.get("vf_coef", ppo_cfg.get("vf_coef", 0.5)))
        self.max_grad_norm = float(
            hyperparameter_overrides.get("max_grad_norm", ppo_cfg.get("max_grad_norm", 0.5))
        )

        net_arch_cfg = ppo_cfg.get("net_arch", {"pi": [256, 256], "vf": [256, 256]})
        self.net_arch = hyperparameter_overrides.get("net_arch", net_arch_cfg)

        # Training & Checkpointing
        self.total_timesteps = int(
            hyperparameter_overrides.get("total_timesteps", ppo_cfg.get("total_timesteps", 100_000))
        )
        self.seed = int(hyperparameter_overrides.get("seed", ppo_cfg.get("seed", 42)))
        self.checkpoint_dir = Path(
            hyperparameter_overrides.get(
                "checkpoint_dir", ppo_cfg.get("checkpoint_dir", "artifacts/models/ppo")
            )
        )
        self.save_freq = int(
            hyperparameter_overrides.get("save_freq", ppo_cfg.get("save_freq", 10000))
        )
        self.eval_freq = int(
            hyperparameter_overrides.get("eval_freq", ppo_cfg.get("eval_freq", 5000))
        )
        self.n_eval_episodes = int(
            hyperparameter_overrides.get("n_eval_episodes", ppo_cfg.get("n_eval_episodes", 10))
        )
        self.verbose = int(hyperparameter_overrides.get("verbose", ppo_cfg.get("verbose", 0)))

        self.dev_mode_cfg = ppo_cfg.get("dev_mode", {})

        self.env = env
        self.model: PPO | None = model

        if self.model is None and self.env is not None:
            self._build_model(self.env)

    def _load_config(
        self,
        config: dict[str, Any] | None,
        config_path: str | Path | None,
    ) -> dict[str, Any]:
        """Load YAML configuration safely."""
        if config is not None:
            return config
        path = Path(config_path) if config_path else Path("config/ppo.yaml")
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("failed_loading_ppo_config", path=str(path), error=str(e))
        return {}

    def _build_model(self, env: gym.Env) -> PPO:
        """Instantiate Stable-Baselines3 PPO model with configured hyperparameters."""
        policy_kwargs = {"net_arch": self.net_arch}

        self.model = PPO(
            policy=self.policy_name,
            env=env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            n_epochs=self.n_epochs,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
            clip_range=self.clip_range,
            ent_coef=self.ent_coef,
            vf_coef=self.vf_coef,
            max_grad_norm=self.max_grad_norm,
            policy_kwargs=policy_kwargs,
            verbose=self.verbose,
            seed=self.seed,
        )
        return self.model

    def train(
        self,
        env: gym.Env | None = None,
        total_timesteps: int | None = None,
        dev_mode: bool = False,
        condition: str = "default",
        checkpoint_dir: str | Path | None = None,
        save_checkpoints: bool = True,
        callbacks: list[BaseCallback] | None = None,
    ) -> PPOTrainingResult:
        """Train the PPO defense agent on the simulation environment."""
        target_env = env or self.env
        if target_env is None:
            raise ValueError("An environment must be provided for PPO training.")

        if self.model is None:
            if dev_mode:
                self.n_steps = min(self.n_steps, 128)
                self.batch_size = min(self.batch_size, 32)
            self._build_model(target_env)
        elif env is not None:
            self.model.set_env(target_env)

        if total_timesteps is not None:
            timesteps = total_timesteps
        elif dev_mode:
            timesteps = int(self.dev_mode_cfg.get("total_timesteps", 10_000))
        else:
            timesteps = self.total_timesteps

        ckpt_path = Path(checkpoint_dir or self.checkpoint_dir)
        ckpt_path.mkdir(parents=True, exist_ok=True)

        cb_list = list(callbacks) if callbacks else []
        recorded_checkpoints: list[str] = []

        if save_checkpoints and self.save_freq > 0 and timesteps >= self.save_freq:
            ckpt_cb = CheckpointCallback(
                save_freq=self.save_freq,
                save_path=str(ckpt_path),
                name_prefix=f"ppo_{condition}_step",
                verbose=self.verbose,
            )
            cb_list.append(ckpt_cb)

        logger.info(
            "starting_ppo_training",
            timesteps=timesteps,
            condition=condition,
            dev_mode=dev_mode,
            checkpoint_dir=str(ckpt_path),
        )

        start_time = time.time()
        self.model.learn(
            total_timesteps=timesteps,
            callback=cb_list if cb_list else None,
            progress_bar=False,
        )
        duration = time.time() - start_time

        final_model_name = f"ppo_{condition}_final.zip"
        final_model_path = ckpt_path / final_model_name
        self.model.save(str(final_model_path.with_suffix("")))
        recorded_checkpoints.append(str(final_model_path))

        eval_result = self.evaluate(target_env, n_episodes=self.n_eval_episodes)

        training_result = PPOTrainingResult(
            model_path=str(final_model_path),
            total_timesteps=timesteps,
            training_duration_seconds=duration,
            condition=condition,
            checkpoints=recorded_checkpoints,
            final_eval_reward=eval_result.mean_reward,
            mitigation_rate=eval_result.mitigation_rate,
            hyperparameters=self.get_hyperparameters(),
        )

        logger.info(
            "ppo_training_completed",
            duration=duration,
            eval_reward=eval_result.mean_reward,
            mitigation_rate=eval_result.mitigation_rate,
            model_path=str(final_model_path),
        )

        return training_result

    def predict(
        self,
        observation: np.ndarray,
        state: Any = None,
        episode_start: Any = None,
        deterministic: bool = True,
    ) -> tuple[int, Any]:
        """Predict defensive action given an environment observation vector."""
        if self.model is None:
            return int(DefenseAction.MONITOR), None

        action, next_state = self.model.predict(
            observation,
            state=state,
            episode_start=episode_start,
            deterministic=deterministic,
        )
        if isinstance(action, np.ndarray):
            action_int = int(action.item() if action.ndim == 0 else action[0])
        else:
            action_int = int(action)

        return action_int, next_state

    def evaluate(
        self,
        env: gym.Env,
        n_episodes: int = 50,
        seed: int | None = None,
    ) -> PPOEvaluationResult:
        """Run benchmark evaluation over multiple simulation episodes."""
        episodes = n_episodes or self.n_eval_episodes
        eval_seed = seed if seed is not None else self.seed

        episode_rewards: list[float] = []
        episode_lengths: list[int] = []
        availability_samples: list[float] = []
        action_counts = {DefenseAction.get_name(a): 0 for a in range(5)}
        mitigated_count = 0
        catastrophic_count = 0

        for ep in range(episodes):
            ep_seed = eval_seed + ep
            obs, info = env.reset(seed=ep_seed)
            ep_reward = 0.0
            steps = 0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                steps += 1
                action, _ = self.predict(obs, deterministic=True)
                action_name = DefenseAction.get_name(action)
                action_counts[action_name] += 1

                obs, reward, terminated, truncated, step_info = env.step(action)
                ep_reward += float(reward)
                availability_samples.append(float(step_info.get("mean_health", 1.0)))

            episode_rewards.append(ep_reward)
            episode_lengths.append(steps)

            if step_info.get("mitigated", False):
                mitigated_count += 1
            if step_info.get("catastrophic_failure", False):
                catastrophic_count += 1

        mean_reward = float(np.mean(episode_rewards)) if episode_rewards else 0.0
        std_reward = float(np.std(episode_rewards)) if episode_rewards else 0.0
        mitigation_rate = float(mitigated_count / episodes) if episodes > 0 else 0.0
        mean_avail = float(np.mean(availability_samples)) if availability_samples else 1.0
        mean_len = float(np.mean(episode_lengths)) if episode_lengths else 0.0

        return PPOEvaluationResult(
            model_name="ppo_agent",
            n_episodes=episodes,
            mean_reward=mean_reward,
            std_reward=std_reward,
            mitigation_rate=mitigation_rate,
            mean_availability=mean_avail,
            mean_episode_length=mean_len,
            action_distribution=action_counts,
            episode_rewards=episode_rewards,
            mitigated_episodes=mitigated_count,
            catastrophic_failures=catastrophic_count,
        )

    def save(self, path: str | Path) -> Path:
        """Save the underlying PPO model weights."""
        if self.model is None:
            raise ValueError("Cannot save uninitialized model.")
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        base_path = save_path.with_suffix("") if save_path.suffix == ".zip" else save_path
        self.model.save(str(base_path))
        return save_path if save_path.suffix == ".zip" else save_path.with_suffix(".zip")

    @classmethod
    def load(
        cls,
        path: str | Path,
        env: gym.Env | None = None,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
    ) -> PPODefenseAgent:
        """Load a trained PPO model from disk."""
        agent = cls(config=config, config_path=config_path, env=env)
        agent.model = PPO.load(str(path), env=env)
        return agent

    def get_hyperparameters(self) -> dict[str, Any]:
        """Return dictionary of active PPO hyperparameters."""
        return {
            "algorithm": self.algorithm,
            "policy": self.policy_name,
            "learning_rate": self.learning_rate,
            "n_steps": self.n_steps,
            "batch_size": self.batch_size,
            "n_epochs": self.n_epochs,
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "clip_range": self.clip_range,
            "ent_coef": self.ent_coef,
            "vf_coef": self.vf_coef,
            "max_grad_norm": self.max_grad_norm,
            "net_arch": self.net_arch,
            "seed": self.seed,
        }
