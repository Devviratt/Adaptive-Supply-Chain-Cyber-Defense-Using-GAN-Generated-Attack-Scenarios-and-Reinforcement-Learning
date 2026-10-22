"""
ASCCD Rule-Based Baseline Defense Policy.

Implements a deterministic, heuristic operational cybersecurity defense
playbook. Serves as the scientific benchmark (Experiment A) for evaluating
the value added by adaptive reinforcement learning policies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import structlog
import yaml

from src.baselines.models import BaselineEvaluationResult
from src.environment.models import DefenseAction

logger = structlog.get_logger(__name__)


class RuleBasedDefensePolicy:
    """Deterministic heuristic defense policy conforming to standard cybersecurity playbooks.

    Evaluates supply-chain health and threat indicators sequentially:
      1. Recovery Needed: Restore service availability when risk is neutralised.
      2. Integrity Severely Compromised: Clean reconstruction (rebuild) when risk is critical.
      3. High Active Threat: Block incoming malicious traffic when high risk/critical attack.
      4. Early Warning: Isolate stage to quarantine lateral spread when moderate risk.
      5. Normal Operation: Passive monitoring and logging when all stages are clean.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
    ) -> None:
        """Initialize the rule-based defense policy."""
        self.config = self._load_config(config, config_path)
        base_cfg = self.config.get("baseline", {})
        self.name = base_cfg.get("name", "rule_based")
        self.description = base_cfg.get("description", "Deterministic rule-based defense policy.")
        self.n_eval_episodes = int(base_cfg.get("n_eval_episodes", 100))
        self.seed = int(base_cfg.get("seed", 42))

        # Configurable decision thresholds
        self.thresholds = {
            "recovery_min_availability": 0.40,
            "recovery_max_risk": 0.30,
            "rebuild_risk": 0.70,
            "rebuild_health_critical": 0.25,
            "block_risk": 0.50,
            "block_severity": 0.75,  # high or critical
            "isolate_risk": 0.25,
            "isolate_propagation": 0.60,
        }

    def _load_config(
        self,
        config: dict[str, Any] | None,
        config_path: str | Path | None,
    ) -> dict[str, Any]:
        """Load YAML configuration safely."""
        if config is not None:
            return config
        path = Path(config_path) if config_path else Path("config/baseline.yaml")
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("failed_loading_baseline_config", path=str(path), error=str(e))
        return {}

    def predict(
        self,
        observation: np.ndarray,
        state: Any = None,
        episode_start: Any = None,
        deterministic: bool = True,
    ) -> tuple[int, None]:
        """Select defensive action based on 12-dimensional observation vector.

        Matches Stable-Baselines3 policy API signature for drop-in interchangeability.

        Args:
            observation: 12-dimensional float32 observation vector.
            state: Optional recurrent policy state (unused for rule-based).
            episode_start: Optional episode start flag (unused).
            deterministic: Deterministic flag (always True for rule-based).

        Returns:
            Tuple of (action_int, None).
        """
        # Ensure 1D array
        obs = np.asarray(observation).flatten()
        if len(obs) < 12:
            # Fallback if observation space differs
            return int(DefenseAction.MONITOR), None

        # Unpack observation
        # [0, 1]: supplier health, risk
        # [2, 3]: build health, risk
        # [4, 5]: registry health, risk
        # [6, 7]: deployment health, risk
        healths = [obs[0], obs[2], obs[4], obs[6]]
        risks = [obs[1], obs[3], obs[5], obs[7]]
        severity = obs[8]
        propagation = obs[10]

        max_risk = max(risks)
        min_health = min(healths)
        t = self.thresholds

        # Rule 1: Recovery Needed
        # If any service availability is severely degraded but risk is suppressed
        if min_health < t["recovery_min_availability"] and max_risk < t["recovery_max_risk"]:
            return int(DefenseAction.RECOVER), None

        # Rule 2: Integrity Compromised / Rebuild Needed
        # If threat level is critical or stage is severely compromised
        if max_risk >= t["rebuild_risk"] or (min_health < t["rebuild_health_critical"] and max_risk >= 0.40):
            return int(DefenseAction.REBUILD), None

        # Rule 3: High Threat / Volumetric Flood -> Block
        # If active attack is high/critical severity or high localized risk
        if max_risk >= t["block_risk"] or severity >= t["block_severity"]:
            return int(DefenseAction.BLOCK), None

        # Rule 4: Moderate Risk / Propagation Threat -> Isolate
        # Early containment to prevent lateral spread along dependency chain
        if max_risk >= t["isolate_risk"] or propagation >= t["isolate_propagation"]:
            return int(DefenseAction.ISOLATE), None

        # Rule 5: Low Risk / Clean State -> Monitor
        return int(DefenseAction.MONITOR), None

    def evaluate(
        self,
        env: gym.Env,
        n_episodes: int | None = None,
        seed: int | None = None,
    ) -> BaselineEvaluationResult:
        """Run systematic evaluation of the baseline policy over multiple episodes.

        Args:
            env: SupplyChainEnv instance.
            n_episodes: Total evaluation episodes (default: from config, 100).
            seed: Initial random seed.

        Returns:
            BaselineEvaluationResult containing comprehensive benchmark metrics.
        """
        episodes = n_episodes or self.n_eval_episodes
        eval_seed = seed if seed is not None else self.seed

        episode_rewards: list[float] = []
        episode_lengths: list[int] = []
        availability_samples: list[float] = []
        action_counts = {
            DefenseAction.get_name(a): 0 for a in range(5)
        }
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
                action, _ = self.predict(obs)
                action_name = DefenseAction.get_name(action)
                action_counts[action_name] += 1

                obs, reward, terminated, truncated, step_info = env.step(action)
                ep_reward += reward
                availability_samples.append(step_info.get("mean_health", 1.0))

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

        return BaselineEvaluationResult(
            policy_name=self.name,
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
