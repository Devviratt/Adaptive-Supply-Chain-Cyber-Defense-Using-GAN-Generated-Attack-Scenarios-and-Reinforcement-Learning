"""
ASCCD Attack Scenario Models.

Defines domain data structures, enums, and representations for
supply-chain cyber-defense scenarios.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class SupplyChainStage(str, Enum):
    """Four core stages of the software supply chain lifecycle."""

    SUPPLIER = "supplier"
    BUILD = "build"
    REGISTRY = "registry"
    DEPLOYMENT = "deployment"


class AttackSeverity(str, Enum):
    """Discrete severity levels for attack scenarios."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AttackScenario:
    """Structured representation of a supply chain attack scenario.

    Maps tabular network attack telemetry into actionable supply-chain
    cyber-defense semantics for simulation and reinforcement learning.
    """

    scenario_id: str
    attack_category: str
    severity: str  # low, medium, high, critical
    affected_stage: str  # supplier, build, registry, deployment
    propagation_risk: float  # [0.0, 1.0]
    availability_impact: float  # [0.0, 1.0]
    integrity_impact: float  # [0.0, 1.0]
    confidentiality_impact: float  # [0.0, 1.0]
    duration_steps: int  # [1, max_steps]
    source: str = "real"  # "real" or "synthetic"
    feature_vector: dict[str, float] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate and clamp numeric boundaries."""
        if not self.scenario_id:
            self.scenario_id = f"scen_{uuid.uuid4().hex[:12]}"

        # Normalize and validate strings
        self.attack_category = str(self.attack_category).strip().lower()
        self.severity = str(self.severity).strip().lower()
        self.affected_stage = str(self.affected_stage).strip().lower()
        self.source = str(self.source).strip().lower()

        # Clamp float impact metrics to [0.0, 1.0]
        self.propagation_risk = float(np.clip(self.propagation_risk, 0.0, 1.0))
        self.availability_impact = float(np.clip(self.availability_impact, 0.0, 1.0))
        self.integrity_impact = float(np.clip(self.integrity_impact, 0.0, 1.0))
        self.confidentiality_impact = float(np.clip(self.confidentiality_impact, 0.0, 1.0))

        # Clamp duration steps
        self.duration_steps = max(1, int(self.duration_steps))

    def to_dict(self) -> dict[str, Any]:
        """Convert scenario to dictionary representation."""
        return asdict(self)

    def to_vector(self) -> np.ndarray:
        """Extract a normalized semantic feature vector for RL observation or embedding.

        Vector composition (8 dimensions):
        [
            propagation_risk,
            availability_impact,
            integrity_impact,
            confidentiality_impact,
            stage_index / 3.0,
            severity_index / 3.0,
            duration_steps / 50.0,
            is_synthetic (0.0 or 1.0)
        ]
        """
        stages = ["supplier", "build", "registry", "deployment"]
        severities = ["low", "medium", "high", "critical"]

        stage_idx = stages.index(self.affected_stage) if self.affected_stage in stages else 3
        sev_idx = severities.index(self.severity) if self.severity in severities else 1
        is_synth = 1.0 if self.source == "synthetic" else 0.0

        return np.array(
            [
                self.propagation_risk,
                self.availability_impact,
                self.integrity_impact,
                self.confidentiality_impact,
                float(stage_idx) / 3.0,
                float(sev_idx) / 3.0,
                float(min(self.duration_steps, 50)) / 50.0,
                is_synth,
            ],
            dtype=np.float32,
        )

    def to_orm(self) -> Any:
        """Convert to SQLAlchemy ORM Scenario model instance."""
        from src.common.models import Scenario

        scenario_orm = Scenario(
            scenario_id=self.scenario_id,
            attack_category=self.attack_category,
            severity=self.severity,
            affected_stage=self.affected_stage,
            propagation_risk=self.propagation_risk,
            availability_impact=self.availability_impact,
            integrity_impact=self.integrity_impact,
            confidentiality_impact=self.confidentiality_impact,
            source=self.source,
            duration_steps=self.duration_steps,
        )
        scenario_orm.set_features(self.feature_vector)
        return scenario_orm

    @classmethod
    def from_orm(cls, orm_scenario: Any) -> AttackScenario:
        """Create an AttackScenario from an ORM Scenario model instance."""
        features = orm_scenario.get_features() if hasattr(orm_scenario, "get_features") else {}
        return cls(
            scenario_id=orm_scenario.scenario_id,
            attack_category=orm_scenario.attack_category,
            severity=orm_scenario.severity,
            affected_stage=orm_scenario.affected_stage,
            propagation_risk=orm_scenario.propagation_risk,
            availability_impact=orm_scenario.availability_impact,
            integrity_impact=orm_scenario.integrity_impact,
            confidentiality_impact=orm_scenario.confidentiality_impact,
            duration_steps=orm_scenario.duration_steps,
            source=orm_scenario.source,
            feature_vector=features,
        )
