"""
Integration tests — to be expanded as modules are implemented.

Phase 1: Basic API integration tests.
Future phases will add: data pipeline, GAN pipeline, RL pipeline tests.
"""


class TestAPIIntegration:
    """Integration tests for the FastAPI backend."""

    def test_health_then_project_flow(self, api_client):
        """Health check + project status should work in sequence."""
        # Step 1: Health check
        health_resp = api_client.get("/api/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        # Step 2: Readiness (checks DB)
        ready_resp = api_client.get("/api/health/ready")
        assert ready_resp.status_code == 200

        # Step 3: Project status
        status_resp = api_client.get("/api/project/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["team_number"] == 84

        # Step 4: Team info
        team_resp = api_client.get("/api/project/team")
        assert team_resp.status_code == 200
        assert len(team_resp.json()["members"]) == 3

    def test_invalid_endpoint_returns_error(self, api_client):
        """Non-existent endpoints should return 404."""
        response = api_client.get("/api/nonexistent")
        assert response.status_code == 404
