"""
ASCCD Pydantic Schemas for Attack Scenarios.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ScenarioResponse(BaseModel):
    """Schema for returning structured attack scenario details."""

    scenario_id: str
    name: str | None = None
    attack_category: str
    affected_stage: str
    severity: str
    propagation_risk: float
    availability_impact: float
    integrity_impact: float
    confidentiality_impact: float
    source: str
    duration_steps: int
    description: str = ""


class ScenarioMapRequest(BaseModel):
    """Schema for mapping raw network flow features into an AttackScenario."""

    features: dict[str, Any] = Field(default_factory=dict)
    label: str = Field(default="DDoS")
    source: str = Field(default="custom")


class ScenarioListResponse(BaseModel):
    """Schema for listing scenarios with pagination."""

    total: int
    scenarios: list[ScenarioResponse]
