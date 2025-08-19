import pytest
from fastapi.testclient import TestClient


@pytest.mark.simple
class TestSimple:
    """Simple test cases for basic functionality."""

    def test_string_manipulation(self):
        """Test simple string manipulation function."""
        def format_phone_number(phone: str) -> str:
            """Simple utility function to format phone numbers."""
            # Remove any non-digit characters
            digits_only = ''.join(filter(str.isdigit, phone))
            
            # Format as: +1-XXX-XXX-XXXX for 10-11 digit numbers
            if len(digits_only) == 10:
                return f"+1-{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
            elif len(digits_only) == 11 and digits_only[0] == '1':
                return f"+{digits_only[0]}-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:]}"
            else:
                return digits_only
        
        # Test cases
        assert format_phone_number("1234567890") == "+1-123-456-7890"
        assert format_phone_number("11234567890") == "+1-123-456-7890" 
        assert format_phone_number("(123) 456-7890") == "+1-123-456-7890"
        assert format_phone_number("123-456-7890") == "+1-123-456-7890"
        assert format_phone_number("123.456.7890") == "+1-123-456-7890"

    def test_math_operations(self):
        """Test simple mathematical operations."""
        def calculate_confidence_percentage(score: float) -> int:
            """Convert confidence score to percentage."""
            if score < 0:
                return 0
            elif score > 1:
                return 100
            else:
                return int(score * 100)
        
        # Test cases
        assert calculate_confidence_percentage(0.85) == 85
        assert calculate_confidence_percentage(0.0) == 0
        assert calculate_confidence_percentage(1.0) == 100
        assert calculate_confidence_percentage(-0.1) == 0
        assert calculate_confidence_percentage(1.5) == 100
        assert calculate_confidence_percentage(0.999) == 99

    def test_api_root_endpoint(self, client):
        """Test the root API endpoint returns expected response."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Legalink WhatsApp Agent API"
        assert isinstance(data["message"], str)

    def test_api_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "legalink-whatsapp-agent"
        
        # Verify response structure
        assert len(data) == 2
        assert all(isinstance(value, str) for value in data.values())

    def test_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404