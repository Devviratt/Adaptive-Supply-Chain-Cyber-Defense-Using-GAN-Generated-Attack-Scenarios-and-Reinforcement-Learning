"""
ASCCD Pydantic Schemas for Supply-Chain Environment Simulation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StageStatusSchema(BaseModel):
    """Schema for individual supply chain stage state."""

    name: str
    health: float
    risk: float = 0.0
    criticality: float = 1.0
    is_compromised: bool = False
    is_isolated: bool = False
    is_blocked: bool = False


class SimulationResetRequest(BaseModel):
    """Request schema for resetting simulation environment."""

    seed: int | None = Field(default=None, description="Optional random seed")
    scenario_id: str | None = Field(default=None, description="Optional specific scenario to simulate")


class SimulationStepRequest(BaseModel):
    """Request schema for taking an action in the simulation environment."""

    action: int = Field(ge=0, le=4, description="Defense action (0: Monitor, 1: Isolate, 2: Block, 3: Rebuild, 4: Recover)")


class SimulationStepResponse(BaseModel):
    """Response schema following environment step execution."""

    observation: list[float]
    reward: float
    terminated: bool
    truncated: bool
    stages: dict[str, StageStatusSchema]
    action_taken: str
    step_info: dict[str, Any]
