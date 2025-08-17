import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestMainAPI:
    """Test cases for the main API endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Legalink WhatsApp Agent API"}

    def test_health_endpoint(self, client):
        """Test the health endpoint returns service status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "legalink-whatsapp-agent"

    def test_app_metadata(self, client):
        """Test that the app has correct metadata."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Legalink WhatsApp Agent API"
        assert data["info"]["version"] == "0.1.0"