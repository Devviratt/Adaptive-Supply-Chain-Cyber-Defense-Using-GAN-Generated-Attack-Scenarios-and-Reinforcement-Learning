"""
ASCCD Database Models.

ORM models for scenarios, experiments, metrics, simulation runs,
training runs, and system events.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base, TimestampMixin


class Scenario(Base, TimestampMixin):
    """Attack scenario record (real or synthetic)."""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    attack_category: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))  # low, medium, high, critical
    affected_stage: Mapped[str] = mapped_column(String(32))  # supplier, build, registry, deployment
    propagation_risk: Mapped[float] = mapped_column(Float, default=0.0)
    availability_impact: Mapped[float] = mapped_column(Float, default=0.0)
    integrity_impact: Mapped[float] = mapped_column(Float, default=0.0)
    confidentiality_impact: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(16))  # real, synthetic
    feature_vector: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_steps: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("ix_scenario_category", "attack_category"),
        Index("ix_scenario_source", "source"),
    )

    def set_features(self, features: dict) -> None:
        """Serialize feature vector to JSON."""
        self.feature_vector = json.dumps(features)

    def get_features(self) -> dict:
        """Deserialize feature vector from JSON."""
        if self.feature_vector:
            return json.loads(self.feature_vector)
        return {}


class Experiment(Base, TimestampMixin):
    """Experiment run record."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model_type: Mapped[str] = mapped_column(String(32))  # rule_based, dqn, dqn_gan, ppo
    dataset_version: Mapped[str] = mapped_column(String(64), default="v1")
    seed: Mapped[int] = mapped_column(Integer, default=42)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON config
    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending, running, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    metrics: Mapped[list[ExperimentMetric]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    simulation_runs: Mapped[list[SimulationRun]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )

    def set_config(self, config: dict) -> None:
        """Serialize config to JSON."""
        self.config = json.dumps(config)

    def get_config(self) -> dict:
        """Deserialize config from JSON."""
        if self.config:
            return json.loads(self.config)
        return {}


class ExperimentMetric(Base):
    """Individual metric recording for an experiment."""

    __tablename__ = "experiment_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"))
    metric_name: Mapped[str] = mapped_column(String(64))
    metric_value: Mapped[float] = mapped_column(Float)
    episode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    experiment: Mapped[Experiment] = relationship(back_populates="metrics")

    __table_args__ = (
        Index("ix_metric_name", "metric_name"),
        Index("ix_metric_experiment", "experiment_id"),
    )


class SimulationRun(Base):
    """Individual simulation episode record."""

    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"))
    episode: Mapped[int] = mapped_column(Integer)
    initial_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_reward: Mapped[float] = mapped_column(Float, default=0.0)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(
        String(32), default="unknown"
    )  # mitigated, compromised, timeout
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    experiment: Mapped[Experiment] = relationship(back_populates="simulation_runs")


class TrainingRun(Base, TimestampMixin):
    """ML model training run record."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_type: Mapped[str] = mapped_column(String(32))  # ctgan, dqn, ppo
    config: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    checkpoint_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    best_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class SystemEvent(Base):
    """System event log entry."""

    __tablename__ = "system_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(
        String(32)
    )  # info, warning, error, training, experiment
    severity: Mapped[str] = mapped_column(String(16), default="info")
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_event_type", "event_type"),
        Index("ix_event_created", "created_at"),
    )

    def set_metadata(self, data: dict) -> None:
        """Serialize metadata to JSON."""
        self.metadata_json = json.dumps(data)

    def get_metadata(self) -> dict:
        """Deserialize metadata from JSON."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
