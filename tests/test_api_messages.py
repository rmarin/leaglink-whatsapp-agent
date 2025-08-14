import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid


@pytest.mark.api
class TestMessagesAPI:
    """Test cases for the messages API endpoints."""

    def test_create_message_success(self, client):
        """Test successful message creation."""
        message_data = {
            "content": "¿Cuáles son mis derechos laborales?",
            "sender": "1234567890"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == message_data["content"]
        assert data["sender"] == message_data["sender"]
        assert "id" in data
        assert "timestamp" in data
        
        # Verify ID is valid UUID format
        uuid.UUID(data["id"])
        
        # Verify timestamp can be parsed
        datetime.fromisoformat(data["timestamp"])

    def test_create_message_missing_content(self, client):
        """Test message creation with missing content."""
        message_data = {
            "sender": "1234567890"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_message_missing_sender(self, client):
        """Test message creation with missing sender."""
        message_data = {
            "content": "Test message"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_message_empty_content(self, client):
        """Test message creation with empty content."""
        message_data = {
            "content": "",
            "sender": "1234567890"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_message_empty_sender(self, client):
        """Test message creation with empty sender."""
        message_data = {
            "content": "Test message",
            "sender": ""
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 422  # Validation error

    def test_get_all_messages_empty(self, client):
        """Test getting all messages when none exist."""
        response = client.get("/api/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_all_messages_with_data(self, client):
        """Test getting all messages when some exist."""
        # Create multiple messages
        messages = [
            {"content": "Mensaje 1", "sender": "1111111111"},
            {"content": "Mensaje 2", "sender": "2222222222"},
            {"content": "Mensaje 3", "sender": "3333333333"}
        ]
        
        created_messages = []
        for msg in messages:
            response = client.post("/api/messages", json=msg)
            assert response.status_code == 201
            created_messages.append(response.json())
        
        # Get all messages
        response = client.get("/api/messages")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        for i, message in enumerate(data):
            assert message["content"] == messages[i]["content"]
            assert message["sender"] == messages[i]["sender"]

    def test_get_message_by_id_success(self, client):
        """Test getting a specific message by ID."""
        # Create a message first
        message_data = {
            "content": "Mensaje de prueba",
            "sender": "1234567890"
        }
        
        create_response = client.post("/api/messages", json=message_data)
        assert create_response.status_code == 201
        created_message = create_response.json()
        
        # Get the message by ID
        response = client.get(f"/api/messages/{created_message['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_message["id"]
        assert data["content"] == message_data["content"]
        assert data["sender"] == message_data["sender"]

    def test_get_message_by_id_not_found(self, client):
        """Test getting a message with non-existent ID."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/messages/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_message_by_invalid_id_format(self, client):
        """Test getting a message with invalid ID format."""
        invalid_id = "invalid-uuid-format"
        
        response = client.get(f"/api/messages/{invalid_id}")
        
        # Should still return 404 since the message won't be found
        assert response.status_code == 404

    def test_message_persistence_across_requests(self, client):
        """Test that messages persist across multiple requests."""
        # Create a message
        message_data = {
            "content": "Mensaje persistente",
            "sender": "1234567890"
        }
        
        create_response = client.post("/api/messages", json=message_data)
        assert create_response.status_code == 201
        created_message = create_response.json()
        
        # Verify it appears in get all messages
        all_messages_response = client.get("/api/messages")
        assert all_messages_response.status_code == 200
        all_messages = all_messages_response.json()
        
        found_message = None
        for msg in all_messages:
            if msg["id"] == created_message["id"]:
                found_message = msg
                break
        
        assert found_message is not None
        assert found_message["content"] == message_data["content"]

    def test_multiple_messages_unique_ids(self, client):
        """Test that multiple messages get unique IDs."""
        message_data = {
            "content": "Mensaje repetido",
            "sender": "1234567890"
        }
        
        # Create the same message multiple times
        created_ids = []
        for _ in range(3):
            response = client.post("/api/messages", json=message_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        # All IDs should be unique
        assert len(set(created_ids)) == 3

    def test_message_timestamp_ordering(self, client):
        """Test that message timestamps reflect creation order."""
        messages = [
            {"content": "Primer mensaje", "sender": "1111111111"},
            {"content": "Segundo mensaje", "sender": "2222222222"},
            {"content": "Tercer mensaje", "sender": "3333333333"}
        ]
        
        created_timestamps = []
        for msg in messages:
            response = client.post("/api/messages", json=msg)
            assert response.status_code == 201
            timestamp = response.json()["timestamp"]
            created_timestamps.append(datetime.fromisoformat(timestamp))
        
        # Timestamps should be in order (allowing for some microsecond differences)
        for i in range(1, len(created_timestamps)):
            assert created_timestamps[i] >= created_timestamps[i-1]

    def test_message_content_with_special_characters(self, client):
        """Test message creation with special characters."""
        message_data = {
            "content": "¿Cómo están mis derechos? ¡Necesito ayuda urgente! @#$%^&*()",
            "sender": "1234567890"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == message_data["content"]

    def test_message_long_content(self, client):
        """Test message creation with long content."""
        long_content = "Este es un mensaje muy largo. " * 100  # ~3000 characters
        message_data = {
            "content": long_content,
            "sender": "1234567890"
        }
        
        response = client.post("/api/messages", json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == long_content