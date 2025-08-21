import pytest
import httpx
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestConnections:
    """Test cases for external service connections and connectivity."""

    def test_application_health_endpoint(self, client):
        """Test that the application health endpoint is accessible."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "legalink-whatsapp-agent"

    def test_application_root_endpoint(self, client):
        """Test that the application root endpoint is accessible."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_graph_api_connectivity(self):
        """Test connectivity to Facebook Graph API endpoint."""
        graph_api_base_url = "https://graph.facebook.com"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Test basic connectivity to Graph API (without making actual API calls)
                response = await client.get(f"{graph_api_base_url}/v18.0", 
                                          headers={"User-Agent": "legalink-whatsapp-agent-test"})
                # Graph API should return 400 (missing access token) but connection should work
                assert response.status_code in [400, 401], f"Expected 400/401 but got {response.status_code}"
            except httpx.ConnectError:
                pytest.fail("Could not connect to Facebook Graph API")
            except httpx.TimeoutException:
                pytest.fail("Timeout connecting to Facebook Graph API")

    def test_environment_variables_present(self):
        """Test that required environment variables are available."""
        # These should be set by the mock_env_vars fixture in conftest.py
        assert os.getenv("WEBHOOK_VERIFY_TOKEN") is not None, "WEBHOOK_VERIFY_TOKEN not set"
        assert os.getenv("GRAPH_API_TOKEN") is not None, "GRAPH_API_TOKEN not set"
        assert os.getenv("ANTHROPIC_API_KEY") is not None, "ANTHROPIC_API_KEY not set"

    def test_environment_variables_not_empty(self):
        """Test that required environment variables are not empty."""
        webhook_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
        graph_token = os.getenv("GRAPH_API_TOKEN")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        assert webhook_token and webhook_token.strip(), "WEBHOOK_VERIFY_TOKEN is empty"
        assert graph_token and graph_token.strip(), "GRAPH_API_TOKEN is empty"
        assert anthropic_key and anthropic_key.strip(), "ANTHROPIC_API_KEY is empty"

    @pytest.mark.asyncio
    async def test_httpx_client_basic_functionality(self):
        """Test that httpx client can make basic HTTP requests."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Test with a reliable public endpoint
                response = await client.get("https://httpbin.org/status/200")
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Could not connect to test endpoint (network issue)")
            except httpx.TimeoutException:
                pytest.skip("Timeout connecting to test endpoint (network issue)")

    @pytest.mark.asyncio
    async def test_httpx_client_ssl_verification(self):
        """Test that httpx client properly verifies SSL certificates."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # This should work with proper SSL
                response = await client.get("https://httpbin.org/get")
                assert response.status_code == 200
                
                # This should fail with SSL verification error
                with pytest.raises(httpx.RequestError):
                    await client.get("https://expired.badssl.com/")
            except httpx.ConnectError:
                pytest.skip("Could not connect to test endpoint (network issue)")

    def test_webhook_endpoint_accessible(self, client):
        """Test that webhook endpoint is accessible for verification."""
        # Test webhook verification endpoint
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_value"
        }
        
        response = client.get("/api/webhook", params=params)
        assert response.status_code == 200
        assert response.text == "test_challenge_value"

    @pytest.mark.asyncio
    async def test_graph_api_message_endpoint_structure(self):
        """Test that Graph API message endpoint URL structure is correct."""
        business_phone_number_id = "TEST_PHONE_ID"
        expected_url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
        
        # Verify URL construction matches what the app uses
        from app.api.webhook import send_whatsapp_reply
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {"messages": [{"id": "test_id"}]}
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            await send_whatsapp_reply(
                business_phone_number_id=business_phone_number_id,
                to="1234567890",
                message_text="Test message"
            )
            
            # Verify the URL was called correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == expected_url

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors in HTTP requests."""
        async with httpx.AsyncClient(timeout=1.0) as client:
            # Test with a non-existent domain
            with pytest.raises(httpx.RequestError):
                await client.get("https://this-domain-definitely-does-not-exist-12345.com")

    def test_api_routes_registration(self, client):
        """Test that all expected API routes are properly registered."""
        # Test that OpenAPI spec includes our routes
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that our main endpoints are registered
        assert "/health" in paths
        assert "/" in paths
        assert "/api/webhook" in paths
        assert "/api/messages" in paths