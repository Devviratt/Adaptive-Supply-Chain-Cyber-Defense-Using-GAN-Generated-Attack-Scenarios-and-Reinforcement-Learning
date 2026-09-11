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
