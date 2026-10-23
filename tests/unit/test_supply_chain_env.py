"""
Unit tests for ASCCD Supply Chain Gymnasium Environment (Phase 5).
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
import pytest
from src.environment import DefenseAction, SupplyChainEnv
from src.scenarios.models import AttackScenario


class TestSupplyChainEnvironment:
    """Comprehensive test suite for the custom supply chain Gymnasium environment."""

    @pytest.fixture
    def env(self) -> SupplyChainEnv:
        """Create fresh environment instance."""
        return SupplyChainEnv()

    def test_gym_registration(self) -> None:
        """Verify environment is registered and instantiable via gym.make."""
        env = gym.make("asccd/SupplyChain-v0")
        assert isinstance(env.unwrapped, SupplyChainEnv)
        env.close()

    def test_action_and_observation_spaces(self, env: SupplyChainEnv) -> None:
        """Verify space types, dimensions, and bounds."""
        assert isinstance(env.action_space, gym.spaces.Discrete)
        assert env.action_space.n == 5

        assert isinstance(env.observation_space, gym.spaces.Box)
        assert env.observation_space.shape == (12,)
        assert np.all(env.observation_space.low == 0.0)
        assert np.all(env.observation_space.high == 1.0)

    def test_reset_behavior(self, env: SupplyChainEnv) -> None:
        """Verify reset returns 12-dim observation and valid info dictionary."""
        obs, info = env.reset(seed=42)

        assert isinstance(obs, np.ndarray)
        assert obs.shape == (12,)
        assert np.all(obs >= 0.0) and np.all(obs <= 1.0)

        assert "scenario_id" in info
        assert "affected_stage" in info
        assert "attack_category" in info
        assert env.current_step == 0
        assert env.cumulative_reward == 0.0

    def test_step_returns_gymnasium_5_tuple(self, env: SupplyChainEnv) -> None:
        """Verify step returns (obs, reward, terminated, truncated, info)."""
        env.reset(seed=42)
        obs, reward, terminated, truncated, info = env.step(DefenseAction.MONITOR)

        assert isinstance(obs, np.ndarray)
        assert obs.shape == (12,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
        assert env.current_step == 1

    def test_defense_action_isolate_effects(self, env: SupplyChainEnv) -> None:
        """Verify ISOLATE quarantines the target stage."""
        custom_scen = AttackScenario(
            scenario_id="test_scen_iso",
            attack_category="dos",
            severity="high",
            affected_stage="deployment",
            propagation_risk=0.5,
            availability_impact=0.8,
            integrity_impact=0.1,
            confidentiality_impact=0.05,
            duration_steps=20,
        )
        env.reset(options={"scenario": custom_scen})
        assert env.stages["deployment"].risk > 0.0

        # Execute Isolate action
        obs, reward, terminated, truncated, info = env.step(DefenseAction.ISOLATE)
        assert env.stages["deployment"].is_isolated is True
        assert info["action_taken"] == "Isolate"

    def test_defense_action_block_effects(self, env: SupplyChainEnv) -> None:
        """Verify BLOCK sets is_blocked flag and reduces risk."""
        custom_scen = AttackScenario(
            scenario_id="test_scen_blk",
            attack_category="dos",
            severity="high",
            affected_stage="deployment",
            propagation_risk=0.3,
            availability_impact=0.9,
            integrity_impact=0.1,
            confidentiality_impact=0.05,
            duration_steps=20,
        )
        env.reset(options={"scenario": custom_scen})
        initial_risk = env.stages["deployment"].risk

        obs, reward, terminated, truncated, info = env.step(DefenseAction.BLOCK)
        assert env.stages["deployment"].is_blocked is True
        assert env.stages["deployment"].risk < initial_risk

    def test_defense_action_rebuild_effects(self, env: SupplyChainEnv) -> None:
        """Verify REBUILD clears risk to 0 and restores substantial health."""
        custom_scen = AttackScenario(
            scenario_id="test_scen_reb",
            attack_category="botnet",
            severity="high",
            affected_stage="build",
            propagation_risk=0.8,
            availability_impact=0.4,
            integrity_impact=0.8,
            confidentiality_impact=0.7,
            duration_steps=20,
        )
        env.reset(options={"scenario": custom_scen})
        assert env.stages["build"].risk > 0.0

        obs, reward, terminated, truncated, info = env.step(DefenseAction.REBUILD)
        assert env.stages["build"].risk == 0.0
        assert env.stages["build"].is_compromised is False

    def test_inter_stage_propagation(self, env: SupplyChainEnv) -> None:
        """Verify compromise spreads downstream from supplier to build when unquarantined."""
        custom_scen = AttackScenario(
            scenario_id="test_prop",
            attack_category="web_attack",
            severity="critical",
            affected_stage="supplier",
            propagation_risk=0.9,
            availability_impact=0.2,
            integrity_impact=0.9,
            confidentiality_impact=0.8,
            duration_steps=30,
        )
        env.reset(options={"scenario": custom_scen})
        assert env.stages["build"].risk == 0.0

        # Step with monitor (allowing attack propagation)
        env.step(DefenseAction.MONITOR)
        # Risk should have spread from supplier to build
        assert env.stages["build"].risk > 0.0

    def test_isolation_halts_propagation(self, env: SupplyChainEnv) -> None:
        """Verify isolating supplier prevents spread to build."""
        custom_scen = AttackScenario(
            scenario_id="test_iso_halt",
            attack_category="web_attack",
            severity="critical",
            affected_stage="supplier",
            propagation_risk=0.9,
            availability_impact=0.2,
            integrity_impact=0.9,
            confidentiality_impact=0.8,
            duration_steps=30,
        )
        env.reset(options={"scenario": custom_scen})
        # Isolate supplier immediately
        env.step(DefenseAction.ISOLATE)
        build_risk_step1 = env.stages["build"].risk

        # Take another step while supplier is isolated
        env.step(DefenseAction.MONITOR)
        assert env.stages["build"].risk == pytest.approx(build_risk_step1)

    def test_truncation_at_max_steps(self, env: SupplyChainEnv) -> None:
        """Verify episode truncates when step count reaches max_steps."""
        benign_scen = AttackScenario(
            scenario_id="test_benign",
            attack_category="benign",
            severity="low",
            affected_stage="deployment",
            propagation_risk=0.0,
            availability_impact=0.0,
            integrity_impact=0.0,
            confidentiality_impact=0.0,
            duration_steps=1,
        )
        env.reset(options={"scenario": benign_scen})

        truncated = False
        for _ in range(env.max_steps):
            _, _, terminated, truncated, _ = env.step(DefenseAction.MONITOR)
            if truncated or terminated:
                break

        assert truncated is True
        assert env.current_step == env.max_steps

    def test_unnecessary_action_penalized(self, env: SupplyChainEnv) -> None:
        """Verify taking aggressive actions when benign/clean receives penalty."""
        benign_scen = AttackScenario(
            scenario_id="test_benign_unnec",
            attack_category="benign",
            severity="low",
            affected_stage="deployment",
            propagation_risk=0.0,
            availability_impact=0.0,
            integrity_impact=0.0,
            confidentiality_impact=0.0,
            duration_steps=1,
        )
        env.reset(options={"scenario": benign_scen})
        # Block when everything is clean
        _, reward_block, _, _, _ = env.step(DefenseAction.BLOCK)

        env.reset(options={"scenario": benign_scen})
        # Monitor when everything is clean
        _, reward_monitor, _, _, _ = env.step(DefenseAction.MONITOR)

        # Monitoring should have higher reward than unnecessary blocking
        assert reward_monitor > reward_block

    def test_render_ansi_output(self, env: SupplyChainEnv) -> None:
        """Verify render produces formatted ASCII simulation table."""
        env.reset(seed=42)
        env.step(DefenseAction.MONITOR)
        rendered = env.render()

        assert isinstance(rendered, str)
        assert "ASCCD SUPPLY CHAIN SIMULATION" in rendered
        assert "SUPPLIER" in rendered
        assert "BUILD" in rendered
        assert "REGISTRY" in rendered
        assert "DEPLOYMENT" in rendered

    def test_seed_reproducibility(self, env: SupplyChainEnv) -> None:
        """Verify same random seed produces identical observations."""
        obs1, _ = env.reset(seed=123)
        obs2, _ = env.reset(seed=123)
        np.testing.assert_array_almost_equal(obs1, obs2)
