"""
ASCCD Pydantic Schemas for Defense Policy Decisions and Models.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request schema for predicting an action from an observation vector."""

    observation: list[float] = Field(min_length=12, max_length=12, description="12-dim environment observation vector")
    model_type: str = Field(default="dqn", description="'rule_based', 'dqn', or 'ppo'")
    deterministic: bool = Field(default=True)


class PredictResponse(BaseModel):
    """Response schema for predicted defense action."""

    action: int
    action_name: str
    model_type: str
    timestamp: str


class ModelInfoSchema(BaseModel):
    """Schema for metadata regarding a saved model checkpoint."""

    name: str
    algorithm: str
    path: str
    size_bytes: int
    modified_at: str
