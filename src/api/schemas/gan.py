"""Schemas for synthetic attack generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AttackCategory = Literal[
    "ddos",
    "dos",
    "portscan",
    "botnet",
    "brute_force",
    "web_attack",
    "infiltration",
    "heartbleed",
]
SupplyChainStage = Literal["supplier", "build", "registry", "deployment"]


class SyntheticAttackGenerateRequest(BaseModel):
    """Request to generate examples of one known attack type."""

    attack_category: AttackCategory
    count: int = Field(default=10, ge=1, le=200)
    affected_stage: SupplyChainStage | None = None


class SyntheticAttackGenerateResponse(BaseModel):
    """Summary of generated examples and their mapped simulation incident."""

    attack_category: str
    generated_count: int
    scenario_id: str
    affected_stage: str
    severity: str
