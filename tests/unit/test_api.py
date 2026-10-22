"""
Unit tests for FastAPI endpoints.
"""


class TestHealthEndpoint:
    """Tests for health check endpoints."""

    def test_health_check(self, api_client):
        """GET /api/health should return 200 with status healthy."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ASCCD"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    def test_readiness_check(self, api_client):
        """GET /api/health/ready should return 200 with DB status."""
        response = api_client.get("/api/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ready", "degraded")
        assert "checks" in data
        assert "database" in data["checks"]


class TestProjectEndpoint:
    """Tests for project status endpoints."""

    def test_project_status(self, api_client):
        """GET /api/project/status should return project info."""
        response = api_client.get("/api/project/status")
        assert response.status_code == 200
        data = response.json()
        assert data["team_number"] == 84
        assert "progress" in data
        assert "modules" in data
        assert data["progress"]["total_modules"] > 0

    def test_team_info(self, api_client):
        """GET /api/project/team should return team member info."""
        response = api_client.get("/api/project/team")
        assert response.status_code == 200
        data = response.json()
        assert data["team_number"] == 84
        assert len(data["members"]) == 3

        # Verify all team members present
        names = [m["name"] for m in data["members"]]
        assert "C A Anandavarthan" in names
        assert "Deekshay G" in names
        assert "Dev Virat" in names


class TestOpenAPISpec:
    """Tests for API documentation."""

    def test_openapi_json_available(self, api_client):
        """OpenAPI spec should be accessible."""
        response = api_client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "ASCCD — Adaptive Supply Chain Cyber Defense"


class TestScenariosEndpoint:
    """Tests for attack scenarios endpoints."""

    def test_list_scenarios_empty_or_paginated(self, api_client):
        """GET /api/scenarios should return paginated list."""
        response = api_client.get("/api/scenarios?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "scenarios" in data

    def test_map_flow_record(self, api_client):
        """POST /api/scenarios/map should convert raw features to scenario."""
        payload = {
            "features": {
                "Total Fwd Packets": 100,
                "Flow Duration": 50000,
            },
            "label": "DDoS",
            "source": "api_test",
        }
        response = api_client.post("/api/scenarios/map", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["attack_category"] == "ddos"
        assert data["affected_stage"] == "deployment"
        assert "scenario_id" in data


class TestSimulationEndpoint:
    """Tests for interactive simulation environment endpoints."""

    def test_get_stage_topology(self, api_client):
        """GET /api/simulation/stages should return topology."""
        response = api_client.get("/api/simulation/stages")
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data
        assert "actions" in data
        assert len(data["stages"]) == 4

    def test_reset_and_step_simulation(self, api_client):
        """POST /api/simulation/reset and step should progress environment."""
        # Reset
        reset_resp = api_client.post("/api/simulation/reset", json={"seed": 42})
        assert reset_resp.status_code == 200
        reset_data = reset_resp.json()
        assert len(reset_data["observation"]) == 12
        assert "supplier" in reset_data["stages"]

        # Step
        step_resp = api_client.post("/api/simulation/step", json={"action": 0})
        assert step_resp.status_code == 200
        step_data = step_resp.json()
        assert step_data["action_taken"] == "Monitor"
        assert len(step_data["observation"]) == 12


class TestDefenseEndpoint:
    """Tests for defense prediction and model metadata endpoints."""

    def test_predict_rule_based(self, api_client):
        """POST /api/defense/predict with rule_based should return valid action."""
        clean_obs = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.1]
        response = api_client.post(
            "/api/defense/predict",
            json={"observation": clean_obs, "model_type": "rule_based"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action_name"] == "Monitor"
        assert data["action"] == 0

    def test_list_models(self, api_client):
        """GET /api/defense/models should return list of models."""
        response = api_client.get("/api/defense/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestExperimentsEndpoint:
    """Tests for experiment benchmarking endpoints."""

    def test_list_experiments(self, api_client):
        """GET /api/experiments should return experiment records."""
        response = api_client.get("/api/experiments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_summary_report(self, api_client):
        """GET /api/experiments/summary should return JSON report."""
        response = api_client.get("/api/experiments/summary")
        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data

