"""
Unit tests for ASCCD Attack Scenario Mapper and Scenario Models.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import AttackScenario, AttackSeverity, SupplyChainStage


class TestScenarioModels:
    """Tests for AttackScenario data structure and methods."""

    def test_scenario_creation_and_clamping(self) -> None:
        """Test boundary clamping and normalization of scenario metrics."""
        scenario = AttackScenario(
            scenario_id="test_scen_1",
            attack_category="DOS",
            severity="HIGH",
            affected_stage="DEPLOYMENT",
            propagation_risk=1.5,  # Exceeds 1.0 -> should clamp to 1.0
            availability_impact=-0.2,  # Sub-zero -> should clamp to 0.0
            integrity_impact=0.8,
            confidentiality_impact=0.1,
            duration_steps=0,  # Below 1 -> should clamp to 1
            source="REAL",
        )

        assert scenario.attack_category == "dos"
        assert scenario.severity == "high"
        assert scenario.affected_stage == "deployment"
        assert scenario.source == "real"
        assert scenario.propagation_risk == 1.0
        assert scenario.availability_impact == 0.0
        assert scenario.integrity_impact == 0.8
        assert scenario.confidentiality_impact == 0.1
        assert scenario.duration_steps == 1

    def test_scenario_to_vector(self) -> None:
        """Test conversion to 8-dimensional normalized observation vector."""
        scenario = AttackScenario(
            scenario_id="test_vec",
            attack_category="web_attack",
            severity="high",
            affected_stage="supplier",
            propagation_risk=0.75,
            availability_impact=0.20,
            integrity_impact=0.85,
            confidentiality_impact=0.70,
            duration_steps=25,
            source="synthetic",
        )

        vec = scenario.to_vector()
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (8,)
        assert np.all(vec >= 0.0)
        assert np.all(vec <= 1.0)
        # Check is_synthetic element (last element)
        assert vec[7] == 1.0
        # Supplier stage is index 0 -> 0.0
        assert vec[4] == 0.0

    def test_scenario_orm_roundtrip(self) -> None:
        """Test conversion to and from SQLAlchemy ORM Scenario model."""
        scenario = AttackScenario(
            scenario_id="test_orm_roundtrip",
            attack_category="botnet",
            severity="high",
            affected_stage="build",
            propagation_risk=0.8,
            availability_impact=0.4,
            integrity_impact=0.7,
            confidentiality_impact=0.65,
            duration_steps=20,
            source="real",
            feature_vector={"Flow Duration": 150000.0, "Total Fwd Packets": 12.0},
        )

        orm_model = scenario.to_orm()
        assert orm_model.scenario_id == "test_orm_roundtrip"
        assert orm_model.attack_category == "botnet"
        assert orm_model.affected_stage == "build"
        assert orm_model.get_features() == {"Flow Duration": 150000.0, "Total Fwd Packets": 12.0}

        reconstructed = AttackScenario.from_orm(orm_model)
        assert reconstructed.scenario_id == scenario.scenario_id
        assert reconstructed.attack_category == scenario.attack_category
        assert reconstructed.affected_stage == scenario.affected_stage
        assert reconstructed.propagation_risk == pytest.approx(scenario.propagation_risk)
        assert reconstructed.feature_vector == scenario.feature_vector


class TestScenarioMapper:
    """Tests for ScenarioMapper translation engine."""

    @pytest.fixture
    def mapper(self) -> ScenarioMapper:
        """Fixture returning an initialized ScenarioMapper."""
        return ScenarioMapper()

    def test_default_categories_loaded(self, mapper: ScenarioMapper) -> None:
        """Verify standard attack categories are present."""
        expected = ["web_attack", "brute_force", "botnet", "dos", "ddos", "portscan", "benign"]
        for cat in expected:
            assert cat in mapper.categories

    def test_map_web_attack_targets_supplier(self, mapper: ScenarioMapper) -> None:
        """Web attacks should map to supplier stage with high integrity/confidentiality impact."""
        rec = {"Label": "web_attack", "Flow Duration": 10000.0}
        scen = mapper.map_record(rec, source="real")

        assert scen.attack_category == "web_attack"
        assert scen.affected_stage == SupplyChainStage.SUPPLIER
        assert scen.integrity_impact >= 0.7
        assert scen.confidentiality_impact >= 0.6
        assert scen.propagation_risk >= 0.6

    def test_map_brute_force_targets_build(self, mapper: ScenarioMapper) -> None:
        """Brute force should map to build stage credentials."""
        rec = {"Label": "brute_force", "Flow Duration": 50000.0}
        scen = mapper.map_record(rec, source="real")

        assert scen.attack_category == "brute_force"
        assert scen.affected_stage == SupplyChainStage.BUILD
        assert scen.confidentiality_impact >= 0.7

    def test_map_dos_ddos_targets_deployment(self, mapper: ScenarioMapper) -> None:
        """Volumetric attacks should map to deployment stage with high availability impact."""
        dos_rec = {"Label": "dos", "Flow Bytes/s": 500000.0}
        dos_scen = mapper.map_record(dos_rec)
        assert dos_scen.affected_stage == SupplyChainStage.DEPLOYMENT
        assert dos_scen.availability_impact >= 0.8

        ddos_rec = {"Label": "ddos", "Flow Packets/s": 100000.0}
        ddos_scen = mapper.map_record(ddos_rec)
        assert ddos_scen.affected_stage == SupplyChainStage.DEPLOYMENT
        assert ddos_scen.severity == AttackSeverity.CRITICAL

    def test_map_benign_traffic(self, mapper: ScenarioMapper) -> None:
        """Benign traffic should have zero malicious impact and duration of 1 step."""
        rec = {"Label": "benign", "Flow Duration": 2000.0}
        scen = mapper.map_record(rec)

        assert scen.attack_category == "benign"
        assert scen.availability_impact == 0.0
        assert scen.integrity_impact == 0.0
        assert scen.confidentiality_impact == 0.0
        assert scen.propagation_risk == 0.0
        assert scen.duration_steps == 1

    def test_unknown_label_fallback(self, mapper: ScenarioMapper) -> None:
        """Unknown labels should fall back gracefully without crashing."""
        rec = {"Label": "unknown_zero_day_exploit", "Flow Duration": 1000.0}
        scen = mapper.map_record(rec)

        assert scen.attack_category == "unknown_zero_day_exploit"
        assert scen.severity in ["low", "medium", "high", "critical"]
        assert 0.0 <= scen.propagation_risk <= 1.0

    def test_feature_modulation(self, mapper: ScenarioMapper) -> None:
        """Higher flow volume and duration should increase impact and duration steps."""
        low_rec = {"Label": "dos", "Flow Bytes/s": 10.0, "Flow Duration": 100.0}
        high_rec = {"Label": "dos", "Flow Bytes/s": 1e8, "Flow Duration": 1e8}

        low_scen = mapper.map_record(low_rec)
        high_scen = mapper.map_record(high_rec)

        assert high_scen.availability_impact >= low_scen.availability_impact
        assert high_scen.duration_steps >= low_scen.duration_steps

    def test_map_dataframe_batch(self, mapper: ScenarioMapper) -> None:
        """Test batch mapping from pandas DataFrame."""
        df = pd.DataFrame(
            [
                {"Label": "benign", "Flow Duration": 100},
                {"Label": "dos", "Flow Bytes/s": 2000},
                {"Label": "web_attack", "Flow Duration": 50000},
            ]
        )
        scenarios = mapper.map_dataframe(df, source="synthetic")

        assert len(scenarios) == 3
        assert scenarios[0].attack_category == "benign"
        assert scenarios[1].attack_category == "dos"
        assert scenarios[2].attack_category == "web_attack"
        assert all(s.source == "synthetic" for s in scenarios)

        # Convert back to DataFrame
        scen_df = mapper.to_dataframe(scenarios)
        assert len(scen_df) == 3
        assert "affected_stage" in scen_df.columns
        assert "availability_impact" in scen_df.columns

    def test_database_persistence(self, mapper: ScenarioMapper, db_session) -> None:
        """Test persisting mapped scenarios into SQLite database via SQLAlchemy."""
        from src.common.models import Scenario

        scenarios = [
            mapper.map_record({"Label": "portscan", "Flow Duration": 500}, scenario_id="scen_db_001"),
            mapper.map_record({"Label": "botnet", "Flow Duration": 12000}, scenario_id="scen_db_002"),
        ]

        inserted = mapper.save_to_db(scenarios, db_session)
        assert inserted == 2

        # Verify query from database
        stored = db_session.query(Scenario).all()
        assert len(stored) == 2
        ids = {s.scenario_id for s in stored}
        assert "scen_db_001" in ids
        assert "scen_db_002" in ids

        # Attempt duplicate insertion (should skip without error)
        inserted_again = mapper.save_to_db(scenarios, db_session)
        assert inserted_again == 0

    def test_scenario_streaming_generator(self, mapper: ScenarioMapper) -> None:
        """Test streaming generator for RL environment interaction."""
        df = pd.DataFrame(
            [
                {"Label": "benign"},
                {"Label": "dos"},
                {"Label": "portscan"},
            ]
        )

        stream = mapper.stream_scenarios(df, source="real", loop=False, shuffle=False)
        collected = list(stream)

        assert len(collected) == 3
        assert collected[0].attack_category == "benign"
        assert collected[1].attack_category == "dos"
        assert collected[2].attack_category == "portscan"
