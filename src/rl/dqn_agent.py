"""
ASCCD Deep Q-Network (DQN) Defense Agent.

Implements the reinforcement learning cyber-defense policy using Stable-Baselines3.
Provides high-performance autonomous defense decision-making against supply-chain attacks,
with full checkpointing, evaluation, and serialization capabilities.
"""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import gymnasium as gym
import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
import structlog
import yaml

from src.environment.models import DefenseAction
from src.rl.models import DQNEvaluationResult, DQNTrainingResult

logger = structlog.get_logger(__name__)


class DQNDefenseAgent:
    """Deep Q-Network reinforcement learning agent for supply chain cyber defense.

    Leverages multi-layer perceptron (MLP) Q-networks to map 12-dimensional
    supply-chain health and threat observations into optimal defensive actions:
      - 0: Monitor (Passive telemetry)
      - 1: Isolate (Lateral movement containment)
      - 2: Block (Active vector drop)
      - 3: Rebuild (Clean reconstruction)
      - 4: Recover (Service availability restoration)
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
        env: gym.Env | None = None,
        model: DQN | None = None,
        **hyperparameter_overrides: Any,
    ) -> None:
        """Initialize the DQN defense agent.

        Args:
            config: Optional pre-loaded configuration dictionary.
            config_path: Optional path to YAML configuration file (default: config/dqn.yaml).
            env: Optional Gymnasium environment instance.
            model: Optional pre-existing Stable-Baselines3 DQN model.
            **hyperparameter_overrides: Explicit overrides for any configuration parameters.
        """
        self.config = self._load_config(config, config_path)
        dqn_cfg = self.config.get("dqn", {})

        # Algorithm & Policy
        self.algorithm = dqn_cfg.get("algorithm", "DQN")
        self.policy_name = dqn_cfg.get("policy", "MlpPolicy")

        # Hyperparameters
        self.learning_rate = float(
            hyperparameter_overrides.get("learning_rate", dqn_cfg.get("learning_rate", 1.0e-4))
        )
        self.buffer_size = int(
            hyperparameter_overrides.get("buffer_size", dqn_cfg.get("buffer_size", 100_000))
        )
        self.learning_starts = int(
            hyperparameter_overrides.get("learning_starts", dqn_cfg.get("learning_starts", 1000))
        )
        self.batch_size = int(
            hyperparameter_overrides.get("batch_size", dqn_cfg.get("batch_size", 64))
        )
        self.tau = float(hyperparameter_overrides.get("tau", dqn_cfg.get("tau", 1.0)))
        self.gamma = float(hyperparameter_overrides.get("gamma", dqn_cfg.get("gamma", 0.99)))
        self.train_freq = hyperparameter_overrides.get("train_freq", dqn_cfg.get("train_freq", 4))
        self.gradient_steps = int(
            hyperparameter_overrides.get("gradient_steps", dqn_cfg.get("gradient_steps", 1))
        )
        self.target_update_interval = int(
            hyperparameter_overrides.get(
                "target_update_interval", dqn_cfg.get("target_update_interval", 1000)
            )
        )
        self.exploration_fraction = float(
            hyperparameter_overrides.get(
                "exploration_fraction", dqn_cfg.get("exploration_fraction", 0.2)
            )
        )
        self.exploration_initial_eps = float(
            hyperparameter_overrides.get(
                "exploration_initial_eps", dqn_cfg.get("exploration_initial_eps", 1.0)
            )
        )
        self.exploration_final_eps = float(
            hyperparameter_overrides.get(
                "exploration_final_eps", dqn_cfg.get("exploration_final_eps", 0.05)
            )
        )
        self.net_arch = list(
            hyperparameter_overrides.get("net_arch", dqn_cfg.get("net_arch", [256, 256]))
        )

        # Training & Checkpointing
        self.total_timesteps = int(
            hyperparameter_overrides.get("total_timesteps", dqn_cfg.get("total_timesteps", 100_000))
        )
        self.seed = int(hyperparameter_overrides.get("seed", dqn_cfg.get("seed", 42)))
        self.checkpoint_dir = Path(
            hyperparameter_overrides.get(
                "checkpoint_dir", dqn_cfg.get("checkpoint_dir", "artifacts/models/dqn")
            )
        )
        self.save_freq = int(
            hyperparameter_overrides.get("save_freq", dqn_cfg.get("save_freq", 10000))
        )
        self.eval_freq = int(
            hyperparameter_overrides.get("eval_freq", dqn_cfg.get("eval_freq", 5000))
        )
        self.n_eval_episodes = int(
            hyperparameter_overrides.get("n_eval_episodes", dqn_cfg.get("n_eval_episodes", 10))
        )
        self.tensorboard_log = hyperparameter_overrides.get(
            "tensorboard_log", dqn_cfg.get("tensorboard_log", "experiments/runs/dqn")
        )
        self.verbose = int(hyperparameter_overrides.get("verbose", dqn_cfg.get("verbose", 0)))

        # Dev mode configurations
        self.dev_mode_cfg = dqn_cfg.get("dev_mode", {})

        self.env = env
        self.model: DQN | None = model

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
        path = Path(config_path) if config_path else Path("config/dqn.yaml")
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("failed_loading_dqn_config", path=str(path), error=str(e))
        return {}

    def _build_model(self, env: gym.Env) -> DQN:
        """Instantiate Stable-Baselines3 DQN model with configured hyperparameters."""
        policy_kwargs = {"net_arch": self.net_arch}

        self.model = DQN(
            policy=self.policy_name,
            env=env,
            learning_rate=self.learning_rate,
            buffer_size=self.buffer_size,
            learning_starts=self.learning_starts,
            batch_size=self.batch_size,
            tau=self.tau,
            gamma=self.gamma,
            train_freq=self.train_freq,
            gradient_steps=self.gradient_steps,
            target_update_interval=self.target_update_interval,
            exploration_fraction=self.exploration_fraction,
            exploration_initial_eps=self.exploration_initial_eps,
            exploration_final_eps=self.exploration_final_eps,
            policy_kwargs=policy_kwargs,
            tensorboard_log=self.tensorboard_log if self.tensorboard_log else None,
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
    ) -> DQNTrainingResult:
        """Train the DQN defense agent on the simulation environment.

        Args:
            env: Optional gymnasium environment. If not provided, uses existing self.env.
            total_timesteps: Total environment interaction steps for training.
            dev_mode: If True, uses abbreviated timesteps and buffer size for rapid cycles.
            condition: Experimental condition identifier ('default', 'real_only', 'augmented').
            checkpoint_dir: Directory where checkpoints and the final model are saved.
            save_checkpoints: Whether to save periodic weights checkpoints during training.
            callbacks: Optional list of additional Stable-Baselines3 callbacks.

        Returns:
            DQNTrainingResult dataclass summarizing training outcomes and metrics.
        """
        target_env = env or self.env
        if target_env is None:
            raise ValueError("An environment must be provided for DQN training.")

        # Update or build model if necessary
        if self.model is None:
            if dev_mode:
                self.learning_starts = min(self.learning_starts, 100)
                self.buffer_size = min(self.buffer_size, 10_000)
            self._build_model(target_env)
        elif env is not None:
            self.model.set_env(target_env)

        # Determine training timesteps
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
                name_prefix=f"dqn_{condition}_step",
                verbose=self.verbose,
            )
            cb_list.append(ckpt_cb)

        logger.info(
            "starting_dqn_training",
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

        # Save final trained model
        final_model_name = f"dqn_{condition}_final.zip"
        final_model_path = ckpt_path / final_model_name
        self.model.save(str(final_model_path.with_suffix("")))
        recorded_checkpoints.append(str(final_model_path))

        # Scan directory for generated intermediate checkpoints
        for cp in sorted(ckpt_path.glob(f"dqn_{condition}_step_*.zip")):
            if str(cp) not in recorded_checkpoints:
                recorded_checkpoints.append(str(cp))

        # Post-training evaluation
        eval_result = self.evaluate(target_env, n_episodes=self.n_eval_episodes)

        training_result = DQNTrainingResult(
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
            "dqn_training_completed",
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
        """Predict defensive action given an environment observation vector.

        Matches Stable-Baselines3 and RuleBasedDefensePolicy interface for seamless
        drop-in replacement during evaluation.

        Args:
            observation: 12-dimensional observation vector.
            state: Optional recurrent hidden state (unused in MLP DQN).
            episode_start: Optional episode start indicator.
            deterministic: Whether to take greedy deterministic action or sample with epsilon.

        Returns:
            Tuple of (action_int, state).
        """
        if self.model is None:
            # Fallback to passive monitoring if uninitialized
            return int(DefenseAction.MONITOR), None

        action, next_state = self.model.predict(
            observation,
            state=state,
            episode_start=episode_start,
            deterministic=deterministic,
        )
        # Ensure primitive int output
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
    ) -> DQNEvaluationResult:
        """Run benchmark evaluation over multiple simulation episodes.

        Args:
            env: SupplyChainEnv instance to evaluate on.
            n_episodes: Total episodes to execute.
            seed: Initial random seed for reproducible evaluation.

        Returns:
            DQNEvaluationResult dataclass containing comprehensive performance metrics.
        """
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

        return DQNEvaluationResult(
            model_name="dqn_agent",
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
        """Save the underlying Stable-Baselines3 model weights.

        Args:
            path: Target file path (e.g. 'artifacts/models/dqn/model.zip').

        Returns:
            Saved model Path.
        """
        if self.model is None:
            raise ValueError("Cannot save uninitialized model.")
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # SB3 automatically adds .zip if omitted
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
    ) -> DQNDefenseAgent:
        """Load a trained DQN model from disk.

        Args:
            path: Path to the saved zip file.
            env: Optional Gymnasium environment to bind.
            config: Optional configuration dictionary.
            config_path: Optional path to config YAML.

        Returns:
            Initialized DQNDefenseAgent with loaded weights.
        """
        agent = cls(config=config, config_path=config_path, env=env)
        agent.model = DQN.load(str(path), env=env)
        return agent

    def get_hyperparameters(self) -> dict[str, Any]:
        """Return dictionary of active DQN hyperparameters."""
        return {
            "algorithm": self.algorithm,
            "policy": self.policy_name,
            "learning_rate": self.learning_rate,
            "buffer_size": self.buffer_size,
            "learning_starts": self.learning_starts,
            "batch_size": self.batch_size,
            "tau": self.tau,
            "gamma": self.gamma,
            "train_freq": self.train_freq,
            "gradient_steps": self.gradient_steps,
            "target_update_interval": self.target_update_interval,
            "exploration_fraction": self.exploration_fraction,
            "exploration_initial_eps": self.exploration_initial_eps,
            "exploration_final_eps": self.exploration_final_eps,
            "net_arch": self.net_arch,
            "seed": self.seed,
        }
