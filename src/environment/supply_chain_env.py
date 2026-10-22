"""
ASCCD Supply Chain Gymnasium Environment.

A high-fidelity software supply-chain cyber-defense simulation environment
conforming to the Gymnasium API standard. Simulates dependency propagation,
multi-stage health and compromise dynamics, and adaptive mitigation decisions.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import structlog
import yaml

from src.environment.models import DefenseAction, StageState
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import AttackScenario

logger = structlog.get_logger(__name__)

STAGE_NAMES = ["supplier", "build", "registry", "deployment"]


class SupplyChainEnv(gym.Env):
    """Custom Gymnasium Environment for Software Supply Chain Cyber Defense.

    Observation Space (12 continuous features in [0.0, 1.0]):
      [0]: supplier health
      [1]: supplier risk
      [2]: build health
      [3]: build risk
      [4]: registry health
      [5]: registry risk
      [6]: deployment health
      [7]: deployment risk
      [8]: active attack severity level
      [9]: active attack target stage (normalized index)
      [10]: active attack propagation risk
      [11]: episode step progress (current_step / max_steps)

    Action Space (5 discrete actions):
      0: Monitor — passive telemetry logging (cost: 0.01)
      1: Isolate — quarantine stage to halt inter-stage propagation (cost: 0.15)
      2: Block — block incoming malicious vectors on stage (cost: 0.25)
      3: Rebuild — clean reconstruction from trusted state (cost: 0.35)
      4: Recover — restore traffic and service availability (cost: 0.20)
    """

    metadata = {"render_modes": ["ansi", "human"], "render_fps": 4}

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
        dqn_config_path: str | Path | None = None,
        scenarios: list[AttackScenario] | None = None,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()

        self.render_mode = render_mode
        self.config = self._load_yaml(config, config_path, "config/environment.yaml").get(
            "environment", {}
        )
        self.dqn_config = self._load_yaml(None, dqn_config_path, "config/dqn.yaml")

        # Environment dynamics parameters
        self.max_steps = int(self.config.get("max_steps", 50))
        self.thresholds = self.config.get(
            "thresholds", {"suspicious": 0.3, "compromised": 0.6, "critical": 0.8}
        )
        self.propagation_cfg = self.config.get(
            "propagation",
            {
                "base_rate": 0.1,
                "severity_multiplier": {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0},
            },
        )
        self.recovery_rates = self.config.get(
            "recovery_rates",
            {"monitor": 0.0, "isolate": 0.1, "block": 0.2, "rebuild": 0.5, "recover": 0.4},
        )

        # Reward parameters (from dqn.yaml)
        dqn_reward = self.dqn_config.get("reward", {})
        self.reward_weights = dqn_reward.get(
            "weights",
            {
                "mitigation": 1.0,
                "containment": 0.3,
                "availability": 0.4,
                "impact": -0.5,
                "cost": -0.2,
                "delay": -0.1,
                "unnecessary": -0.3,
            },
        )
        self.reward_values = dqn_reward.get(
            "values",
            {
                "mitigation_success": 10.0,
                "containment_per_stage": 2.0,
                "availability_bonus": 1.0,
                "impact_per_stage": -3.0,
                "step_penalty": -0.1,
            },
        )
        self.action_costs = dqn_reward.get(
            "action_costs",
            {"monitor": 0.01, "isolate": 0.15, "block": 0.25, "rebuild": 0.35, "recover": 0.20},
        )

        # Stage configuration
        self.stage_configs: dict[str, dict[str, float]] = {
            s["name"]: {
                "initial_health": float(s.get("initial_health", 1.0)),
                "criticality": float(s.get("criticality", 1.0)),
            }
            for s in self.config.get(
                "stages",
                [
                    {"name": "supplier", "initial_health": 1.0, "criticality": 0.8},
                    {"name": "build", "initial_health": 1.0, "criticality": 0.9},
                    {"name": "registry", "initial_health": 1.0, "criticality": 0.85},
                    {"name": "deployment", "initial_health": 1.0, "criticality": 1.0},
                ],
            )
        }

        # Spaces definition
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(12,),
            dtype=np.float32,
        )

        # Scenarios pool
        self.scenario_mapper = ScenarioMapper()
        self.scenarios = scenarios or []
        self._scenario_idx = 0

        # Episode runtime state
        self.stages: dict[str, StageState] = {}
        self.active_scenario: AttackScenario | None = None
        self.current_step = 0
        self.cumulative_reward = 0.0
        self.mitigated = False
        self.last_action: int | None = None

        self._init_stages()

    def _load_yaml(
        self,
        explicit_cfg: dict[str, Any] | None,
        explicit_path: str | Path | None,
        default_path_str: str,
    ) -> dict[str, Any]:
        """Load configuration dictionary safely."""
        if explicit_cfg is not None:
            return explicit_cfg
        path = Path(explicit_path) if explicit_path else Path(default_path_str)
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("failed_loading_env_config", path=str(path), error=str(e))
        return {}

    def _init_stages(self) -> None:
        """Initialize all supply chain stages to clean state."""
        self.stages = {}
        for name in STAGE_NAMES:
            cfg = self.stage_configs.get(name, {"initial_health": 1.0, "criticality": 1.0})
            self.stages[name] = StageState(
                name=name,
                health=cfg["initial_health"],
                risk=0.0,
                criticality=cfg["criticality"],
            )

    def _get_obs(self) -> np.ndarray:
        """Construct the 12-dimensional normalized observation vector."""
        obs = np.zeros(12, dtype=np.float32)

        # 1. Stage health and risk (indices 0..7)
        for i, name in enumerate(STAGE_NAMES):
            stage = self.stages[name]
            obs[i * 2] = float(np.clip(stage.health, 0.0, 1.0))
            obs[i * 2 + 1] = float(np.clip(stage.risk, 0.0, 1.0))

        # 2. Active scenario features (indices 8..11)
        if self.active_scenario is not None:
            sev_map = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.0}
            obs[8] = float(sev_map.get(self.active_scenario.severity, 0.5))

            target_idx = (
                STAGE_NAMES.index(self.active_scenario.affected_stage)
                if self.active_scenario.affected_stage in STAGE_NAMES
                else 3
            )
            obs[9] = float(target_idx) / 3.0
            obs[10] = float(np.clip(self.active_scenario.propagation_risk, 0.0, 1.0))
        else:
            obs[8] = 0.0
            obs[9] = 0.0
            obs[10] = 0.0

        # 3. Episode step progress
        progress = float(self.current_step) / float(max(1, self.max_steps))
        obs[11] = float(np.clip(progress, 0.0, 1.0))

        return obs

    def _select_scenario(self) -> AttackScenario:
        """Select or generate an AttackScenario for the episode."""
        if self.scenarios:
            scen = self.scenarios[self._scenario_idx % len(self.scenarios)]
            self._scenario_idx += 1
            return copy.deepcopy(scen)

        # Default synthetic fallback scenario if none provided
        sample_cats = ["dos", "ddos", "web_attack", "brute_force", "botnet", "portscan", "benign"]
        chosen_cat = self.np_random.choice(sample_cats)
        fake_rec = {
            "Label": chosen_cat,
            "Flow Duration": float(self.np_random.uniform(500, 50000)),
            "Flow Bytes/s": float(self.np_random.uniform(100, 100000)),
            "Flow Packets/s": float(self.np_random.uniform(10, 5000)),
        }
        return self.scenario_mapper.map_record(fake_rec, source="synthetic")

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment to initial clean state with a new attack scenario."""
        super().reset(seed=seed)

        self._init_stages()
        self.current_step = 0
        self.cumulative_reward = 0.0
        self.mitigated = False
        self.last_action = None

        # Check options for explicit scenario override
        if options and "scenario" in options:
            self.active_scenario = copy.deepcopy(options["scenario"])
        else:
            self.active_scenario = self._select_scenario()

        # Apply initial attack impact to target stage
        target = self.active_scenario.affected_stage
        if target in self.stages and self.active_scenario.attack_category != "benign":
            init_risk = float(
                np.clip(
                    0.4 + 0.5 * self.active_scenario.propagation_risk,
                    0.3,
                    0.95,
                )
            )
            self.stages[target].risk = init_risk
            self.stages[target].update_status(
                self.thresholds["suspicious"], self.thresholds["compromised"]
            )

        obs = self._get_obs()
        info = {
            "scenario_id": self.active_scenario.scenario_id,
            "attack_category": self.active_scenario.attack_category,
            "affected_stage": self.active_scenario.affected_stage,
            "severity": self.active_scenario.severity,
            "duration_steps": self.active_scenario.duration_steps,
        }

        if self.render_mode == "human":
            print(self.render())

        return obs, info

    def _determine_target_stage(self) -> str:
        """Determine which stage is currently the most urgent target for defense."""
        if not self.active_scenario:
            return "deployment"

        # Prioritize highest risk stage, breaking ties by downstream order
        highest_risk = -1.0
        chosen_stage = self.active_scenario.affected_stage
        for name in reversed(STAGE_NAMES):
            if self.stages[name].risk > highest_risk and self.stages[name].risk > 0.1:
                highest_risk = self.stages[name].risk
                chosen_stage = name

        return chosen_stage if chosen_stage in self.stages else "deployment"

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one environment step with the selected defensive action."""
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action {action}. Must be in {list(range(5))}")

        self.current_step += 1
        self.last_action = action
        target_stage_name = self._determine_target_stage()
        target_stage = self.stages[target_stage_name]

        # 1. Apply Defense Action
        action_name = DefenseAction.get_name(action).lower()
        action_cost = float(self.action_costs.get(action_name, 0.05))

        unnecessary_action = False
        rebuilt_this_step = False
        all_clean = all(s.risk < self.thresholds["suspicious"] for s in self.stages.values())

        if action == DefenseAction.MONITOR:
            # Passive monitoring, zero state disruption
            pass

        elif action == DefenseAction.ISOLATE:
            if all_clean:
                unnecessary_action = True
            target_stage.is_isolated = True
            # Modest stabilization from isolation
            target_stage.health = min(1.0, target_stage.health + 0.10)
            target_stage.risk = max(0.0, target_stage.risk - 0.10)

        elif action == DefenseAction.BLOCK:
            if all_clean:
                unnecessary_action = True
            target_stage.is_blocked = True
            target_stage.health = min(1.0, target_stage.health + 0.20)
            target_stage.risk = max(0.0, target_stage.risk - 0.25)

        elif action == DefenseAction.REBUILD:
            if all_clean:
                unnecessary_action = True
            # Full integrity restore: resets risk and substantially restores health
            target_stage.risk = 0.0
            target_stage.health = min(1.0, target_stage.health + 0.50)
            target_stage.is_isolated = False
            target_stage.is_blocked = False
            rebuilt_this_step = True

        elif action == DefenseAction.RECOVER:
            # Service recovery: re-opens stage and restores availability
            target_stage.is_isolated = False
            target_stage.is_blocked = False
            if target_stage.risk < self.thresholds["suspicious"]:
                target_stage.health = min(1.0, target_stage.health + 0.40)
            else:
                # Recovering a still-compromised stage incurs penalty
                target_stage.risk = min(1.0, target_stage.risk + 0.15)

        # 2. Simulate Attack Impact
        attack_active = (
            self.active_scenario is not None
            and self.active_scenario.attack_category != "benign"
            and self.current_step <= self.active_scenario.duration_steps
            and not rebuilt_this_step
        )

        if attack_active and self.active_scenario:
            attack_stage = self.stages.get(self.active_scenario.affected_stage)
            if attack_stage and not attack_stage.is_blocked:
                # Availability degradation
                avail_drop = (
                    self.active_scenario.availability_impact
                    * attack_stage.criticality
                    * 0.15
                )
                attack_stage.health = max(0.0, attack_stage.health - avail_drop)

                # Integrity / Risk escalation
                risk_inc = self.active_scenario.propagation_risk * 0.10
                attack_stage.risk = min(1.0, attack_stage.risk + risk_inc)

        # 3. Simulate Inter-Stage Dependency Propagation
        # Pipeline order: supplier -> build -> registry -> deployment
        base_rate = float(self.propagation_cfg.get("base_rate", 0.1))
        sev_mults = self.propagation_cfg.get("severity_multiplier", {})
        sev_str = self.active_scenario.severity if self.active_scenario else "medium"
        multiplier = float(sev_mults.get(sev_str, 1.0))

        for i in range(len(STAGE_NAMES) - 1):
            src_name = STAGE_NAMES[i]
            dst_name = STAGE_NAMES[i + 1]
            src_stage = self.stages[src_name]
            dst_stage = self.stages[dst_name]

            # If source stage is compromised and not quarantined
            if (
                src_stage.risk >= self.thresholds["suspicious"]
                and not src_stage.is_isolated
                and not dst_stage.is_isolated
                and not dst_stage.is_blocked
            ):
                spread_amount = base_rate * multiplier * src_stage.risk
                dst_stage.risk = min(1.0, dst_stage.risk + spread_amount)
                dst_stage.health = max(0.0, dst_stage.health - (spread_amount * 0.5))

        # Update all stage statuses
        for s in self.stages.values():
            s.update_status(self.thresholds["suspicious"], self.thresholds["compromised"])

        # 4. Check Mitigation Success
        all_mitigated = all(s.risk < 0.10 for s in self.stages.values())
        if all_mitigated and not self.mitigated and self.active_scenario.attack_category != "benign":
            self.mitigated = True
            mitigation_bonus = float(self.reward_values.get("mitigation_success", 10.0))
        else:
            mitigation_bonus = 0.0

        # 5. Calculate Comprehensive Reward
        w = self.reward_weights
        v = self.reward_values

        # Containment: count stages below suspicious
        contained_stages = sum(1 for s in self.stages.values() if s.risk < self.thresholds["suspicious"])
        containment_rew = contained_stages * float(v.get("containment_per_stage", 2.0))

        # Availability: mean health across all stages
        mean_health = float(np.mean([s.health for s in self.stages.values()]))
        availability_rew = mean_health * float(v.get("availability_bonus", 1.0))

        # Impact penalty: count severely compromised stages
        compromised_stages = sum(1 for s in self.stages.values() if s.risk >= self.thresholds["compromised"])
        impact_penalty = compromised_stages * abs(float(v.get("impact_per_stage", -3.0)))

        # Delay penalty: penalty per step while attack is active
        delay_penalty = abs(float(v.get("step_penalty", -0.1))) if not all_mitigated else 0.0

        # Unnecessary action penalty
        unnecessary_penalty = 1.0 if unnecessary_action else 0.0

        # Reward = w_mit * R_mit + w_cont * R_cont + w_avail * R_avail
        #        + w_imp * P_imp + w_cost * P_cost + w_delay * P_delay + w_unnec * P_unnec
        step_reward = float(
            w.get("mitigation", 1.0) * mitigation_bonus
            + w.get("containment", 0.3) * containment_rew
            + w.get("availability", 0.4) * availability_rew
            + w.get("impact", -0.5) * impact_penalty
            + w.get("cost", -0.2) * action_cost
            + w.get("delay", -0.1) * delay_penalty
            + w.get("unnecessary", -0.3) * unnecessary_penalty
        )

        self.cumulative_reward += step_reward

        # 6. Evaluate Termination & Truncation
        # Termination conditions:
        # A) Attack successfully mitigated and neutralized
        # B) Catastrophic failure: all stages health < 0.15
        catastrophic_failure = all(s.health < 0.15 for s in self.stages.values())
        terminated = bool(self.mitigated or catastrophic_failure)
        truncated = bool(self.current_step >= self.max_steps)

        obs = self._get_obs()
        info = {
            "step": self.current_step,
            "action_taken": DefenseAction.get_name(action),
            "target_stage": target_stage_name,
            "mean_health": round(mean_health, 4),
            "mitigated": self.mitigated,
            "catastrophic_failure": catastrophic_failure,
            "step_reward": round(step_reward, 4),
            "cumulative_reward": round(self.cumulative_reward, 4),
            "stages": {name: s.to_dict() for name, s in self.stages.items()},
        }

        if self.render_mode == "human":
            print(self.render())

        return obs, step_reward, terminated, truncated, info

    def render(self) -> str:
        """Render ASCII representation of supply chain stages and defense state."""
        sep = "=" * 64
        lines = [
            sep,
            f" ASCCD SUPPLY CHAIN SIMULATION — STEP {self.current_step}/{self.max_steps}",
            sep,
        ]

        if self.active_scenario:
            lines.append(
                f" Attack: {self.active_scenario.attack_category.upper():<12} "
                f"Severity: {self.active_scenario.severity.upper():<10} "
                f"Target: {self.active_scenario.affected_stage.upper()}"
            )
        if self.last_action is not None:
            lines.append(f" Last Defense Action: {DefenseAction.get_name(self.last_action).upper()}")

        lines.append("-" * 64)
        lines.append(f" {'STAGE':<12} {'HEALTH':<16} {'RISK':<10} {'STATUS':<12} {'FLAGS'}")
        lines.append("-" * 64)

        for name in STAGE_NAMES:
            s = self.stages[name]
            bars = int(round(s.health * 10))
            health_bar = f"[{'#' * bars}{'-' * (10 - bars)}]"
            status = s.update_status(self.thresholds["suspicious"], self.thresholds["compromised"])

            flags = []
            if s.is_isolated:
                flags.append("ISOLATED")
            if s.is_blocked:
                flags.append("BLOCKED")
            flag_str = " ".join(flags) if flags else "-"

            lines.append(
                f" {name.upper():<12} {health_bar} {s.health*100:4.0f}%   "
                f"{s.risk*100:4.0f}%     {status.upper():<12} {flag_str}"
            )

        lines.append(sep)
        lines.append(f" Cumulative Reward: {self.cumulative_reward:.2f} | Mitigated: {self.mitigated}")
        lines.append(sep)
        return "\n".join(lines)
