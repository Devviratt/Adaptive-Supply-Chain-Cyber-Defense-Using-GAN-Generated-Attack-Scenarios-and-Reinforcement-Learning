"""
ASCCD Pydantic Schemas for Controlled Experiments and Benchmarking.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExperimentRunRequest(BaseModel):
    """Request schema for executing benchmark experiments."""

    experiments: list[str] = Field(default=["A", "B", "C"], description="List of experiment conditions to run")
    episodes: int = Field(default=10, ge=1, le=100)
    dev_mode: bool = Field(default=True)


class ExperimentMetricSchema(BaseModel):
    """Schema for individual recorded experiment metric."""

    name: str
    value: float


class ExperimentItemSchema(BaseModel):
    """Schema for summarized experiment record."""

    id: int
    experiment_id: str
    model_type: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
