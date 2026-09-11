"""
Unit tests for database models.
"""


class TestScenarioModel:
    """Tests for the Scenario ORM model."""

    def test_create_scenario(self, db_session):
        """Should create and persist a scenario."""
        from src.common.models import Scenario

        scenario = Scenario(
            scenario_id="SC-001",
            attack_category="dos",
            severity="high",
            affected_stage="build",
            propagation_risk=0.7,
            availability_impact=0.8,
            integrity_impact=0.3,
            source="real",
        )
        db_session.add(scenario)
        db_session.commit()

        loaded = db_session.query(Scenario).filter_by(scenario_id="SC-001").first()
        assert loaded is not None
        assert loaded.attack_category == "dos"
        assert loaded.severity == "high"
        assert loaded.affected_stage == "build"
        assert loaded.source == "real"

    def test_scenario_feature_serialization(self, db_session):
        """Should serialize and deserialize feature vectors."""
        from src.common.models import Scenario

        scenario = Scenario(
            scenario_id="SC-002",
            attack_category="ddos",
            severity="critical",
            affected_stage="deployment",
            source="synthetic",
        )
        features = {"flow_duration": 0.5, "total_fwd_packets": 100}
        scenario.set_features(features)
        db_session.add(scenario)
        db_session.commit()

        loaded = db_session.query(Scenario).filter_by(scenario_id="SC-002").first()
        loaded_features = loaded.get_features()
        assert loaded_features["flow_duration"] == 0.5
        assert loaded_features["total_fwd_packets"] == 100


class TestExperimentModel:
    """Tests for the Experiment ORM model."""

    def test_create_experiment(self, db_session):
        """Should create an experiment with default status."""
        from src.common.models import Experiment

        exp = Experiment(
            experiment_id="EXP-001",
            model_type="dqn",
            dataset_version="v1",
            seed=42,
        )
        db_session.add(exp)
        db_session.commit()

        loaded = db_session.query(Experiment).filter_by(experiment_id="EXP-001").first()
        assert loaded.status == "pending"
        assert loaded.model_type == "dqn"

    def test_experiment_config_serialization(self, db_session):
        """Should serialize and deserialize experiment config."""
        from src.common.models import Experiment

        exp = Experiment(
            experiment_id="EXP-002",
            model_type="dqn_gan",
            seed=123,
        )
        config = {"learning_rate": 0.001, "episodes": 1000}
        exp.set_config(config)
        db_session.add(exp)
        db_session.commit()

        loaded = db_session.query(Experiment).filter_by(experiment_id="EXP-002").first()
        loaded_config = loaded.get_config()
        assert loaded_config["learning_rate"] == 0.001

    def test_experiment_metric_relationship(self, db_session):
        """Should link metrics to experiments."""
        from src.common.models import Experiment, ExperimentMetric

        exp = Experiment(
            experiment_id="EXP-003",
            model_type="rule_based",
            seed=42,
        )
        db_session.add(exp)
        db_session.commit()

        metric = ExperimentMetric(
            experiment_id=exp.id,
            metric_name="mitigation_success_rate",
            metric_value=0.85,
            episode=10,
        )
        db_session.add(metric)
        db_session.commit()

        loaded = db_session.query(Experiment).filter_by(experiment_id="EXP-003").first()
        assert len(loaded.metrics) == 1
        assert loaded.metrics[0].metric_name == "mitigation_success_rate"
        assert loaded.metrics[0].metric_value == 0.85


class TestSystemEventModel:
    """Tests for the SystemEvent model."""

    def test_create_system_event(self, db_session):
        """Should create a system event with metadata."""
        from src.common.models import SystemEvent

        event = SystemEvent(
            event_type="training",
            severity="info",
            message="DQN training started",
        )
        event.set_metadata({"model": "dqn", "seed": 42})
        db_session.add(event)
        db_session.commit()

        loaded = db_session.query(SystemEvent).first()
        assert loaded.event_type == "training"
        assert loaded.get_metadata()["model"] == "dqn"
