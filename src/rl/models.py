"""
ASCCD Reinforcement Learning Domain Models.

Structures training results, checkpoint tracking, and evaluation metrics
for both Deep Q-Network (DQN) and Proximal Policy Optimization (PPO) defense agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DQNTrainingResult:
    """Artifacts and summary metrics produced by DQN training."""

    model_path: str
    total_timesteps: int
    training_duration_seconds: float
    condition: str = "default"  # "default", "real_only" (Exp B), "augmented" (Exp C)
    checkpoints: list[str] = field(default_factory=list)
    final_eval_reward: float = 0.0
    mitigation_rate: float = 0.0
    hyperparameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert training summary to dictionary."""
        return {
            "model_path": self.model_path,
            "total_timesteps": self.total_timesteps,
            "training_duration_seconds": round(self.training_duration_seconds, 2),
            "condition": self.condition,
            "checkpoints": self.checkpoints,
            "final_eval_reward": round(self.final_eval_reward, 4),
            "mitigation_rate": round(self.mitigation_rate, 4),
            "hyperparameters": self.hyperparameters,
        }


@dataclass
class DQNEvaluationResult:
    """Benchmark evaluation metrics for the trained DQN defense policy."""

    model_name: str
    n_episodes: int
    mean_reward: float
    std_reward: float
    mitigation_rate: float  # [0.0, 1.0] Proportion of mitigated attack scenarios
    mean_availability: float  # [0.0, 1.0] Mean supply chain service uptime
    mean_episode_length: float
    action_distribution: dict[str, int] = field(default_factory=dict)
    episode_rewards: list[float] = field(default_factory=list)
    mitigated_episodes: int = 0
    catastrophic_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert evaluation summary to dictionary."""
        return {
            "model_name": self.model_name,
            "n_episodes": self.n_episodes,
            "mean_reward": round(self.mean_reward, 4),
            "std_reward": round(self.std_reward, 4),
            "mitigation_rate": round(self.mitigation_rate, 4),
            "mean_availability": round(self.mean_availability, 4),
            "mean_episode_length": round(self.mean_episode_length, 2),
            "mitigated_episodes": self.mitigated_episodes,
            "catastrophic_failures": self.catastrophic_failures,
            "action_distribution": self.action_distribution,
        }


@dataclass
class PPOTrainingResult:
    """Artifacts and summary metrics produced by PPO training."""

    model_path: str
    total_timesteps: int
    training_duration_seconds: float
    condition: str = "default"
    checkpoints: list[str] = field(default_factory=list)
    final_eval_reward: float = 0.0
    mitigation_rate: float = 0.0
    hyperparameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert training summary to dictionary."""
        return {
            "model_path": self.model_path,
            "total_timesteps": self.total_timesteps,
            "training_duration_seconds": round(self.training_duration_seconds, 2),
            "condition": self.condition,
            "checkpoints": self.checkpoints,
            "final_eval_reward": round(self.final_eval_reward, 4),
            "mitigation_rate": round(self.mitigation_rate, 4),
            "hyperparameters": self.hyperparameters,
        }


@dataclass
class PPOEvaluationResult:
    """Benchmark evaluation metrics for the trained PPO comparison defense policy."""

    model_name: str
    n_episodes: int
    mean_reward: float
    std_reward: float
    mitigation_rate: float
    mean_availability: float
    mean_episode_length: float
    action_distribution: dict[str, int] = field(default_factory=dict)
    episode_rewards: list[float] = field(default_factory=list)
    mitigated_episodes: int = 0
    catastrophic_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert evaluation summary to dictionary."""
        return {
            "model_name": self.model_name,
            "n_episodes": self.n_episodes,
            "mean_reward": round(self.mean_reward, 4),
            "std_reward": round(self.std_reward, 4),
            "mitigation_rate": round(self.mitigation_rate, 4),
            "mean_availability": round(self.mean_availability, 4),
            "mean_episode_length": round(self.mean_episode_length, 2),
            "mitigated_episodes": self.mitigated_episodes,
            "catastrophic_failures": self.catastrophic_failures,
            "action_distribution": self.action_distribution,
        }
