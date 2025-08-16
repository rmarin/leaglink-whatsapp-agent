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