"""
ASCCD Attack Scenarios API Router.

Endpoints for exploring mapped scenarios, querying scenario attributes,
and dynamically generating supply chain attack scenarios from network flow records.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.scenarios import (
    ScenarioListResponse,
    ScenarioMapRequest,
    ScenarioResponse,
)
from src.common.models import Scenario
from src.scenarios.mapper import ScenarioMapper

router = APIRouter()
mapper = ScenarioMapper()


@router.get("", response_model=ScenarioListResponse)
def list_scenarios(
    category: str | None = Query(None, description="Filter by attack category"),
    source: str | None = Query(None, description="Filter by source (real / synthetic)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ScenarioListResponse:
    """Retrieve paginated list of attack scenarios from the database."""
    query = db.query(Scenario)
    if category:
        query = query.filter(Scenario.attack_category.ilike(f"%{category}%"))
    if source:
        query = query.filter(Scenario.source == source)

    total = query.count()
    records = query.offset(offset).limit(limit).all()

    items = [
        ScenarioResponse(
            scenario_id=r.scenario_id,
            name=getattr(r, "name", None),
            attack_category=r.attack_category,
            affected_stage=r.affected_stage,
            severity=r.severity,
            propagation_risk=r.propagation_risk,
            availability_impact=r.availability_impact,
            integrity_impact=r.integrity_impact,
            confidentiality_impact=r.confidentiality_impact,
            source=r.source,
            duration_steps=r.duration_steps,
            description=r.description or "",
        )
        for r in records
    ]

    return ScenarioListResponse(total=total, scenarios=items)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
) -> ScenarioResponse:
    """Retrieve detailed attributes of a specific attack scenario."""
    r = db.query(Scenario).filter_by(scenario_id=scenario_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    return ScenarioResponse(
        scenario_id=r.scenario_id,
        name=getattr(r, "name", None),
        attack_category=r.attack_category,
        affected_stage=r.affected_stage,
        severity=r.severity,
        propagation_risk=r.propagation_risk,
        availability_impact=r.availability_impact,
        integrity_impact=r.integrity_impact,
        confidentiality_impact=r.confidentiality_impact,
        source=r.source,
        duration_steps=r.duration_steps,
        description=r.description or "",
    )


@router.post("/map", response_model=ScenarioResponse)
def map_flow_record(
    payload: ScenarioMapRequest,
) -> ScenarioResponse:
    """Dynamically map a raw network intrusion record into an AttackScenario."""
    record = dict(payload.features)
    record["Label"] = payload.label

    scen = mapper.map_record(record, source=payload.source)
    return ScenarioResponse(
        scenario_id=scen.scenario_id,
        name=getattr(scen, "name", None),
        attack_category=scen.attack_category,
        affected_stage=scen.affected_stage.value if hasattr(scen.affected_stage, "value") else str(scen.affected_stage),
        severity=scen.severity.value if hasattr(scen.severity, "value") else str(scen.severity),
        propagation_risk=scen.propagation_risk,
        availability_impact=scen.availability_impact,
        integrity_impact=scen.integrity_impact,
        confidentiality_impact=scen.confidentiality_impact,
        source=scen.source,
        duration_steps=scen.duration_steps,
        description=scen.description,
    )
