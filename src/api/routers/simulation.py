"""
ASCCD Simulation API Router.

Interactive endpoints for managing supply-chain simulation sessions,
resetting the environment, and stepping through sequential defensive responses.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.api.schemas.simulation import (
    SimulationResetRequest,
    SimulationStepRequest,
    SimulationStepResponse,
    StageStatusSchema,
)
from src.environment.models import DefenseAction
from src.environment.supply_chain_env import STAGE_NAMES, SupplyChainEnv

router = APIRouter()

# Global interactive simulation environment singleton
_sim_env: SupplyChainEnv | None = None


def get_simulation_env() -> SupplyChainEnv:
    """Get or lazily initialize the active simulation environment."""
    global _sim_env
    if _sim_env is None:
        _sim_env = SupplyChainEnv()
    return _sim_env


def _format_stages(env: SupplyChainEnv) -> dict[str, StageStatusSchema]:
    """Format environment stages into API schema."""
    res = {}
    for name, st in env.stages.items():
        res[name] = StageStatusSchema(
            name=name,
            health=round(float(st.health), 4),
            risk=round(float(st.risk), 4),
            criticality=round(float(st.criticality), 4),
            is_compromised=bool(st.is_compromised),
            is_isolated=bool(st.is_isolated),
            is_blocked=bool(st.is_blocked),
        )
    return res


@router.post("/reset", response_model=SimulationStepResponse)
def reset_simulation(payload: SimulationResetRequest | None = None) -> SimulationStepResponse:
    """Reset the simulation environment to an initial attack state."""
    env = get_simulation_env()
    seed = payload.seed if payload else None
    obs, info = env.reset(seed=seed)

    return SimulationStepResponse(
        observation=[round(float(x), 4) for x in obs],
        reward=0.0,
        terminated=False,
        truncated=False,
        stages=_format_stages(env),
        action_taken="NONE",
        step_info=info,
    )


@router.post("/step", response_model=SimulationStepResponse)
def step_simulation(payload: SimulationStepRequest) -> SimulationStepResponse:
    """Execute a single defensive action in the simulation environment."""
    env = get_simulation_env()
    action = payload.action
    action_name = DefenseAction.get_name(action)

    obs, reward, terminated, truncated, step_info = env.step(action)

    return SimulationStepResponse(
        observation=[round(float(x), 4) for x in obs],
        reward=round(float(reward), 4),
        terminated=bool(terminated),
        truncated=bool(truncated),
        stages=_format_stages(env),
        action_taken=action_name,
        step_info=step_info,
    )


@router.get("/stages")
def get_stage_topology() -> dict[str, Any]:
    """Retrieve supply-chain stage topology and dependency structure."""
    return {
        "stages": STAGE_NAMES,
        "dependencies": [
            {"from": "supplier", "to": "build"},
            {"from": "build", "to": "registry"},
            {"from": "registry", "to": "deployment"},
        ],
        "actions": [
            {"id": 0, "name": "Monitor", "cost": 0.01, "description": "Passive telemetry logging"},
            {"id": 1, "name": "Isolate", "cost": 0.15, "description": "Quarantine stage to prevent lateral spread"},
            {"id": 2, "name": "Block", "cost": 0.25, "description": "Drop active attack traffic vectors"},
            {"id": 3, "name": "Rebuild", "cost": 0.35, "description": "Clean reconstruction from verified state"},
            {"id": 4, "name": "Recover", "cost": 0.20, "description": "Restore service availability and throughput"},
        ],
    }
