"""
ASCCD Baseline Domain Models.

Structures evaluation results and metric summaries for baseline defense policies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BaselineEvaluationResult:
    """Evaluation summary metrics for a baseline defense policy."""

    policy_name: str
    n_episodes: int
    mean_reward: float
    std_reward: float
    mitigation_rate: float  # [0.0, 1.0] Proportion of successfully resolved incidents
    mean_availability: float  # [0.0, 1.0] Mean supply chain service uptime
    mean_episode_length: float
    action_distribution: dict[str, int] = field(default_factory=dict)
    episode_rewards: list[float] = field(default_factory=list)
    mitigated_episodes: int = 0
    catastrophic_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result summary to dictionary representation."""
        return {
            "policy_name": self.policy_name,
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
