"""
ASCCD Evaluation Domain Models.

Structures experimental conditions, evaluation results, metric aggregates,
and comparative benchmarks across Experiments A (Baseline), B (DQN Real),
C (DQN Augmented), and D (PPO Comparison).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExperimentResult:
    """Benchmark results for a single experimental condition."""

    experiment_id: str  # "A", "B", "C", "D"
    name: str  # e.g. "Rule-Based Baseline", "DQN without GAN", "DQN with GAN"
    model_type: str  # "rule_based", "dqn", "dqn_gan", "ppo"
    dataset: str  # "real", "real+synthetic"
    n_episodes: int
    seeds: list[int] = field(default_factory=list)

    # Security Metrics
    mitigation_success_rate: float = 0.0  # [0.0, 1.0] Proportion of attacks successfully neutralized
    containment_rate: float = 0.0  # [0.0, 1.0] Proportion of attacks contained without propagating
    attack_impact_score: float = 0.0  # Aggregate damage caused to stages (lower is better)

    # Availability Metrics
    service_availability: float = 1.0  # [0.0, 1.0] Mean supply-chain service uptime
    total_downtime_steps: int = 0  # Cumulative steps with any stage unavailable

    # Decision Quality Metrics
    unnecessary_intervention_rate: float = 0.0  # Costly actions taken during benign states
    avg_response_steps: float = 0.0  # Mean steps elapsed before first defensive action
    action_distribution: dict[str, int] = field(default_factory=dict)

    # Reinforcement Learning Metrics
    mean_reward: float = 0.0
    std_reward: float = 0.0
    reward_variance: float = 0.0
    episode_rewards: list[float] = field(default_factory=list)

    # Robustness & Category breakdown
    performance_by_attack_class: dict[str, dict[str, float]] = field(default_factory=dict)
    catastrophic_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert result metrics to a serializable dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "model_type": self.model_type,
            "dataset": self.dataset,
            "n_episodes": self.n_episodes,
            "seeds": self.seeds,
            "security": {
                "mitigation_success_rate": round(self.mitigation_success_rate, 4),
                "containment_rate": round(self.containment_rate, 4),
                "attack_impact_score": round(self.attack_impact_score, 4),
                "catastrophic_failures": self.catastrophic_failures,
            },
            "availability": {
                "service_availability": round(self.service_availability, 4),
                "total_downtime_steps": self.total_downtime_steps,
            },
            "decision_quality": {
                "unnecessary_intervention_rate": round(self.unnecessary_intervention_rate, 4),
                "avg_response_steps": round(self.avg_response_steps, 2),
                "action_distribution": self.action_distribution,
            },
            "rl": {
                "mean_reward": round(self.mean_reward, 4),
                "std_reward": round(self.std_reward, 4),
                "reward_variance": round(self.reward_variance, 4),
            },
            "performance_by_attack_class": self.performance_by_attack_class,
        }


@dataclass
class ComparisonSummary:
    """Comparative benchmark summary across all executed experiment conditions."""

    experiments: dict[str, ExperimentResult] = field(default_factory=dict)
    relative_gains: dict[str, dict[str, float]] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert comparison summary to serializable dictionary."""
        return {
            "timestamp": self.timestamp,
            "experiments": {exp_id: exp.to_dict() for exp_id, exp in self.experiments.items()},
            "relative_gains": self.relative_gains,
        }
