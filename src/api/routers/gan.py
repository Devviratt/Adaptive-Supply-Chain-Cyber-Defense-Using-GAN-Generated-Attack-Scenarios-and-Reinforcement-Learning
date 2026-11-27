"""Endpoints for creating synthetic attack examples for the simulator."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.gan import (
    SyntheticAttackGenerateRequest,
    SyntheticAttackGenerateResponse,
)
from src.gan.ctgan import generate_ctgan
from src.scenarios.mapper import ScenarioMapper

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_MODEL_PATH = (
    PROJECT_ROOT / "artifacts" / "models" / "ctgan" / "cicids2017_sample" / "model.pkl"
)
DEFAULT_MODEL_PATH = PROJECT_ROOT / "artifacts" / "models" / "ctgan" / "model.pkl"
MODEL_PATH = SAMPLE_MODEL_PATH if SAMPLE_MODEL_PATH.is_file() else DEFAULT_MODEL_PATH
GENERATED_PATH = PROJECT_ROOT / "data" / "generated" / "ui_synthetic_attacks.csv"


@router.post("/generate", response_model=SyntheticAttackGenerateResponse)
def generate_synthetic_attack(
    payload: SyntheticAttackGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SyntheticAttackGenerateResponse:
    """Generate synthetic rows, map them to incidents, and save them for simulation."""
    if not MODEL_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail=(
                "The synthetic attack model is not available. Train it with "
                "`python scripts/train_ctgan_demo.py train` before generating examples."
            ),
        )

    try:
        generated = generate_ctgan(
            model_path=MODEL_PATH,
            output_path=GENERATED_PATH,
            count=payload.count,
            seed=uuid.uuid4().int % (2**32),
            per_class={payload.attack_category: payload.count},
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    mapper = ScenarioMapper(config_path=PROJECT_ROOT / "config" / "scenario.yaml")
    scenarios = [
        mapper.map_record(
            row,
            source="synthetic",
            scenario_id=f"scen_synthetic_{uuid.uuid4().hex[:12]}",
            affected_stage=payload.affected_stage,
        )
        for row in generated.to_dict(orient="records")
    ]
    mapper.save_to_db(scenarios, db)

    representative = scenarios[0]
    return SyntheticAttackGenerateResponse(
        attack_category=representative.attack_category,
        generated_count=len(generated),
        scenario_id=representative.scenario_id,
        affected_stage=(
            representative.affected_stage.value
            if hasattr(representative.affected_stage, "value")
            else str(representative.affected_stage)
        ),
        severity=(
            representative.severity.value
            if hasattr(representative.severity, "value")
            else str(representative.severity)
        ),
    )
