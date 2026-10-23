"""
Unit tests for ASCCD Rule-Based Baseline Defense Policy (Phase 6).
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
import pytest
from src.baselines import BaselineEvaluationResult, RuleBasedDefensePolicy
from src.environment import DefenseAction


class TestRuleBasedDefensePolicy:
    """Comprehensive unit test suite for the deterministic heuristic defense policy."""

    @pytest.fixture
    def policy(self) -> RuleBasedDefensePolicy:
        """Create fresh policy instance."""
        return RuleBasedDefensePolicy()

    def test_policy_initialization(self, policy: RuleBasedDefensePolicy) -> None:
        """Verify policy attributes and threshold initialization."""
        assert policy.name == "rule_based"
        assert policy.n_eval_episodes > 0
        assert "recovery_min_availability" in policy.thresholds

    def test_predict_clean_state_selects_monitor(self, policy: RuleBasedDefensePolicy) -> None:
        """When all stages are clean and healthy, policy should monitor passively."""
        # 12-dim observation: all healths 1.0, all risks 0.0, severity 0.0, target 0.0, prop 0.0, step 0.0
        clean_obs = np.array(
            [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.1],
            dtype=np.float32,
        )
        action, state = policy.predict(clean_obs)
        assert action == int(DefenseAction.MONITOR)
        assert state is None

    def test_predict_recovery_needed_selects_recover(self, policy: RuleBasedDefensePolicy) -> None:
        """When availability is degraded but risk is resolved, policy should recover service."""
        # Deployment health is 0.30, but all risks are 0.0
        recovery_obs = np.array(
            [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.30, 0.0, 0.0, 0.0, 0.0, 0.3],
            dtype=np.float32,
        )
        action, _ = policy.predict(recovery_obs)
        assert action == int(DefenseAction.RECOVER)

    def test_predict_critical_compromise_selects_rebuild(self, policy: RuleBasedDefensePolicy) -> None:
        """When a stage is critically compromised (risk >= 0.70), policy should rebuild."""
        # Build stage risk is 0.85
        rebuild_obs = np.array(
            [1.0, 0.0, 0.6, 0.85, 1.0, 0.0, 1.0, 0.0, 0.75, 0.33, 0.5, 0.2],
            dtype=np.float32,
        )
        action, _ = policy.predict(rebuild_obs)
        assert action == int(DefenseAction.REBUILD)

    def test_predict_high_threat_selects_block(self, policy: RuleBasedDefensePolicy) -> None:
        """When risk is high or severity is critical, policy should block traffic."""
        # Deployment risk is 0.55
        block_obs = np.array(
            [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.7, 0.55, 0.8, 1.0, 0.4, 0.1],
            dtype=np.float32,
        )
        action, _ = policy.predict(block_obs)
        assert action == int(DefenseAction.BLOCK)

    def test_predict_moderate_risk_selects_isolate(self, policy: RuleBasedDefensePolicy) -> None:
        """When risk is moderate (>= 0.25), policy should isolate for containment."""
        # Supplier risk is 0.30
        isolate_obs = np.array(
            [0.9, 0.30, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.3, 0.1],
            dtype=np.float32,
        )
        action, _ = policy.predict(isolate_obs)
        assert action == int(DefenseAction.ISOLATE)

    def test_evaluate_policy_execution(self, policy: RuleBasedDefensePolicy) -> None:
        """Verify systematic evaluation loop produces valid summary metrics."""
        env = gym.make("asccd/SupplyChain-v0")
        results = policy.evaluate(env, n_episodes=5, seed=42)
        env.close()

        assert isinstance(results, BaselineEvaluationResult)
        assert results.policy_name == "rule_based"
        assert results.n_episodes == 5
        assert isinstance(results.mean_reward, float)
        assert 0.0 <= results.mitigation_rate <= 1.0
        assert 0.0 <= results.mean_availability <= 1.0
        assert results.mean_episode_length > 0
        assert len(results.episode_rewards) == 5

        # Check action distribution
        assert isinstance(results.action_distribution, dict)
        total_actions = sum(results.action_distribution.values())
        assert total_actions > 0

    def test_result_to_dict(self) -> None:
        """Verify BaselineEvaluationResult serialization to dictionary."""
        res = BaselineEvaluationResult(
            policy_name="test_policy",
            n_episodes=10,
            mean_reward=15.5,
            std_reward=2.1,
            mitigation_rate=0.90,
            mean_availability=0.95,
            mean_episode_length=4.2,
            action_distribution={"Monitor": 5, "Block": 10},
            mitigated_episodes=9,
            catastrophic_failures=0,
        )
        d = res.to_dict()
        assert d["policy_name"] == "test_policy"
        assert d["mean_reward"] == 15.5
        assert d["mitigation_rate"] == 0.90
        assert d["mitigated_episodes"] == 9

    def test_evaluation_reproducibility(self, policy: RuleBasedDefensePolicy) -> None:
        """Verify identical seed produces identical evaluation results."""
        env = gym.make("asccd/SupplyChain-v0")
        res1 = policy.evaluate(env, n_episodes=3, seed=100)
        res2 = policy.evaluate(env, n_episodes=3, seed=100)
        env.close()

        assert res1.mean_reward == pytest.approx(res2.mean_reward)
        assert res1.mitigation_rate == pytest.approx(res2.mitigation_rate)
        assert res1.episode_rewards == pytest.approx(res2.episode_rewards)
