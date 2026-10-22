"""
ASCCD Supply Chain Environment Module.

Exports the custom Gymnasium simulation environment and registers
the gymnasium environment ID 'asccd/SupplyChain-v0'.
"""

import gymnasium as gym

from src.environment.models import DefenseAction, StageState
from src.environment.supply_chain_env import STAGE_NAMES, SupplyChainEnv

# Register environment with Gymnasium
gym.register(
    id="asccd/SupplyChain-v0",
    entry_point="src.environment.supply_chain_env:SupplyChainEnv",
    max_episode_steps=50,
)

__all__ = [
    "DefenseAction",
    "STAGE_NAMES",
    "StageState",
    "SupplyChainEnv",
]
