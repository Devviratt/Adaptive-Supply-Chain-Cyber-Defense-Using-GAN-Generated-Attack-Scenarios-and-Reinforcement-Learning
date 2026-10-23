"""
ASCCD Experiments and Benchmarking API Router.

Endpoints for inspecting completed controlled experiments, querying summary metrics,
and triggering fresh benchmark runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.experiments import ExperimentItemSchema, ExperimentRunRequest
from src.common.models import Experiment
from src.evaluation.engine import EvaluationEngine

router = APIRouter()
engine = EvaluationEngine()


@router.get("", response_model=list[ExperimentItemSchema])
def list_experiments(db: Session = Depends(get_db)) -> list[ExperimentItemSchema]:
    """Retrieve all recorded experiment runs and their associated metric scores."""
    records = db.query(Experiment).order_by(Experiment.id.desc()).all()
    results: list[ExperimentItemSchema] = []

    for r in records:
        metrics_dict: dict[str, float] = {}
        for m in r.metrics:
            metrics_dict[m.metric_name] = round(float(m.metric_value), 4)

        results.append(
            ExperimentItemSchema(
                id=r.id,
                experiment_id=r.experiment_id,
                model_type=r.model_type,
                status=r.status,
                started_at=r.started_at.isoformat() if r.started_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                metrics=metrics_dict,
            )
        )

    return results


@router.get("/summary")
def get_experiments_summary() -> dict[str, Any]:
    """Retrieve the latest comparative benchmarks summary report JSON."""
    report_file = Path("artifacts/reports/experiments_summary.json")
    if not report_file.exists():
        return {
            "status": "pending",
            "message": "No experiments have been executed yet.",
            "experiments": {},
            "comparison": {},
        }

    with open(report_file, encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.post("/run")
def trigger_experiments(
    payload: ExperimentRunRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Execute a set of benchmark experiments (e.g. A, B, C) and return comparative results."""
    summary = engine.run_all_experiments(
        experiment_ids=payload.experiments,
        n_episodes=payload.episodes,
        dev_mode=payload.dev_mode,
        session=db,
    )
    engine.export_reports(summary)
    return summary.to_dict()
