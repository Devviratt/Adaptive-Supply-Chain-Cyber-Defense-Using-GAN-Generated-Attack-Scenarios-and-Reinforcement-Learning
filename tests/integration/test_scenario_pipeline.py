"""
Integration test for ASCCD Scenario Mapping Pipeline (Phase 4).

Tests the end-to-end integration between processed attack dataset,
ScenarioMapper, JSON export, and database persistence.
"""

import json
from pathlib import Path

import pandas as pd
from src.common.models import Scenario
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import SupplyChainStage


def test_end_to_end_scenario_pipeline(tmp_path: Path, db_session) -> None:
    """Test full scenario mapping workflow from CSV input to DB persistence and JSON report."""
    # 1. Create realistic processed dataset fixture
    csv_file = tmp_path / "processed_test_sample.csv"
    data = [
        {"Label": "benign", "Flow Duration": 150.0, "Flow Bytes/s": 200.0, "Total Fwd Packets": 2},
        {"Label": "dos", "Flow Duration": 8000.0, "Flow Bytes/s": 450000.0, "Total Fwd Packets": 120},
        {"Label": "ddos", "Flow Duration": 12000.0, "Flow Packets/s": 60000.0, "Total Fwd Packets": 300},
        {"Label": "web_attack", "Flow Duration": 2500.0, "Flow Bytes/s": 1200.0, "Total Fwd Packets": 15},
        {"Label": "brute_force", "Flow Duration": 1800.0, "Flow Bytes/s": 900.0, "Total Fwd Packets": 8},
        {"Label": "botnet", "Flow Duration": 5500.0, "Flow Bytes/s": 2500.0, "Total Fwd Packets": 25},
        {"Label": "portscan", "Flow Duration": 300.0, "Flow Bytes/s": 150.0, "Total Fwd Packets": 4},
    ]
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)

    # 2. Execute Mapper
    mapper = ScenarioMapper()
    scenarios = mapper.map_dataframe(df, source="real")
    assert len(scenarios) == 7

    # 3. Check Supply Chain Stages Allocation
    stages = {s.affected_stage for s in scenarios}
    assert SupplyChainStage.SUPPLIER in stages
    assert SupplyChainStage.BUILD in stages
    assert SupplyChainStage.DEPLOYMENT in stages

    # 4. Export to JSON
    json_path = tmp_path / "scenarios.json"
    with open(json_path, "w") as f:
        json.dump([s.to_dict() for s in scenarios], f)

    assert json_path.exists()
    with open(json_path) as f:
        loaded_json = json.load(f)
    assert len(loaded_json) == 7

    # 5. Persist to Database
    inserted = mapper.save_to_db(scenarios, db_session)
    assert inserted == 7

    # 6. Verify ORM retrieval and feature consistency
    db_scenarios = db_session.query(Scenario).all()
    assert len(db_scenarios) == 7
    categories = {s.attack_category for s in db_scenarios}
    assert "dos" in categories
    assert "web_attack" in categories
    assert "botnet" in categories

    dos_db = db_session.query(Scenario).filter_by(attack_category="dos").first()
    assert dos_db is not None
    assert dos_db.affected_stage == "deployment"
    assert dos_db.availability_impact > 0.5
