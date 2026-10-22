"""
ASCCD Supply Chain Environment Domain Models.

Defines stage states, action spaces, and state representations
for the software supply chain simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np


class DefenseAction(IntEnum):
    """Discrete defensive actions available to the defense agent."""

    MONITOR = 0  # Passive observation, telemetry logging (Cost: 0.01)
    ISOLATE = 1  # Network quarantine of stage to halt propagation (Cost: 0.15)
    BLOCK = 2  # Block malicious attack vectors / traffic (Cost: 0.25)
    REBUILD = 3  # Clean rebuild from known-good base / container (Cost: 0.35)
    RECOVER = 4  # Restore service availability and traffic routing (Cost: 0.20)

    @classmethod
    def get_name(cls, action: int) -> str:
        """Return human-readable action name."""
        names = {
            cls.MONITOR: "Monitor",
            cls.ISOLATE: "Isolate",
            cls.BLOCK: "Block",
            cls.REBUILD: "Rebuild",
            cls.RECOVER: "Recover",
        }
        return names.get(action, "Unknown")


@dataclass
class StageState:
    """State of an individual software supply chain dependency stage."""

    name: str  # supplier, build, registry, deployment
    health: float = 1.0  # [0.0, 1.0] Availability and operational integrity
    risk: float = 0.0  # [0.0, 1.0] Threat level / active compromise
    criticality: float = 1.0  # Relative importance in supply chain
    is_isolated: bool = False  # Whether stage is quarantined from peers
    is_blocked: bool = False  # Whether incoming attack traffic is blocked
    is_compromised: bool = False  # True when risk exceeds compromised threshold

    def __post_init__(self) -> None:
        """Clamp numeric boundaries."""
        self.health = float(np.clip(self.health, 0.0, 1.0))
        self.risk = float(np.clip(self.risk, 0.0, 1.0))
        self.criticality = float(np.clip(self.criticality, 0.1, 1.0))

    def update_status(self, suspicious_th: float = 0.3, compromised_th: float = 0.6) -> str:
        """Update and return semantic stage status."""
        if self.health <= 0.1:
            return "offline"
        if self.risk >= compromised_th:
            self.is_compromised = True
            return "compromised"
        if self.risk >= suspicious_th:
            return "suspicious"
        self.is_compromised = False
        return "normal"

    def to_dict(self) -> dict[str, Any]:
        """Convert stage state to dictionary representation."""
        return {
            "name": self.name,
            "health": round(self.health, 4),
            "risk": round(self.risk, 4),
            "criticality": self.criticality,
            "is_isolated": self.is_isolated,
            "is_blocked": self.is_blocked,
            "is_compromised": self.is_compromised,
        }
