"""
Integration test for ASCCD Supply Chain Gymnasium Environment (Phase 5).

Tests end-to-end integration between processed attack dataset,
ScenarioMapper, and SupplyChainEnv simulation episodes.
"""

from __future__ import annotations

import gymnasium as gym
import pandas as pd
from src.environment import DefenseAction
from src.scenarios.mapper import ScenarioMapper


def test_supply_chain_env_with_mapped_scenarios() -> None:
    """Test full integration: dataset -> ScenarioMapper -> SupplyChainEnv multi-step simulation."""
    # 1. Create realistic dataset sample
    df = pd.DataFrame(
        [
            {"Label": "dos", "Flow Duration": 15000.0, "Flow Bytes/s": 500000.0, "Total Fwd Packets": 100},
            {"Label": "web_attack", "Flow Duration": 8000.0, "Flow Bytes/s": 1200.0, "Total Fwd Packets": 20},
            {"Label": "botnet", "Flow Duration": 12000.0, "Flow Bytes/s": 3500.0, "Total Fwd Packets": 35},
        ]
    )

    # 2. Map scenarios
    mapper = ScenarioMapper()
    scenarios = mapper.map_dataframe(df, source="real")
    assert len(scenarios) == 3

    # 3. Initialize Gymnasium Environment with mapped scenarios
    env = gym.make("asccd/SupplyChain-v0", scenarios=scenarios)
    obs, info = env.reset(seed=42)

    assert obs.shape == (12,)
    assert info["attack_category"] in ["dos", "web_attack", "botnet"]

    # 4. Step through simulation with defense actions
    actions = [
        DefenseAction.MONITOR,
        DefenseAction.ISOLATE,
        DefenseAction.BLOCK,
        DefenseAction.REBUILD,
        DefenseAction.RECOVER,
    ]

    total_reward = 0.0
    for action in actions:
        obs, reward, terminated, truncated, step_info = env.step(action)
        total_reward += reward
        assert obs.shape == (12,)
        assert isinstance(reward, float)
        if terminated or truncated:
            break

    # 5. Check environment state consistency
    rendered = env.render()
    assert "ASCCD SUPPLY CHAIN SIMULATION" in rendered
    assert step_info["step"] > 0
    env.close()
