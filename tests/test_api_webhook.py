import pytest
from unittest.mock import AsyncMock, patch, Mock
import json


@pytest.mark.api
@pytest.mark.webhook
class TestWebhookAPI:
    """Test cases for the WhatsApp webhook API endpoints."""

    def test_verify_webhook_success(self, client):
        """Test successful webhook verification."""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_123"
        }
        
        response = client.get("/api/webhook", params=params)
        
        assert response.status_code == 200
        assert response.text == "test_challenge_123"

    def test_verify_webhook_wrong_mode(self, client):
        """Test webhook verification with wrong mode."""
        params = {
            "hub.mode": "unsubscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_123"
        }
        
        response = client.get("/api/webhook", params=params)
        
        assert response.status_code == 403

    def test_verify_webhook_wrong_token(self, client):
        """Test webhook verification with wrong verify token."""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "test_challenge_123"
        }
        
        response = client.get("/api/webhook", params=params)
        
        assert response.status_code == 403

    def test_verify_webhook_missing_parameters(self, client):
        """Test webhook verification with missing parameters."""
        # Missing hub.mode
        params = {
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_123"
        }
        
        response = client.get("/api/webhook", params=params)
        
        assert response.status_code == 422  # Validation error

    @patch('app.api.webhook.get_legal_agent')
    @patch('app.api.webhook.process_legal_query')
    @patch('app.api.webhook.send_whatsapp_reply')
    @patch('app.api.webhook.mark_message_as_read')
    async def test_receive_webhook_text_message(
        self, 
        mock_mark_read, 
        mock_send_reply, 
        mock_process_query, 
        mock_get_agent,
        client, 
        sample_whatsapp_webhook_payload
    ):
        """Test receiving a text message through webhook."""
        # Setup mocks
        mock_agent = AsyncMock()
        mock_get_agent.return_value = mock_agent
        mock_process_query.return_value = "Esta es la respuesta del agente legal"
        mock_send_reply.return_value = AsyncMock()
        mock_mark_read.return_value = AsyncMock()
        
        response = client.post("/api/webhook", json=sample_whatsapp_webhook_payload)
        
        assert response.status_code == 200

    def test_receive_webhook_no_message(self, client):
        """Test receiving webhook payload without message."""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550559999",
                                    "phone_number_id": "PHONE_NUMBER_ID"
                                }
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        response = client.post("/api/webhook", json=payload)
        
        assert response.status_code == 200

    def test_receive_webhook_non_text_message(self, client, sample_whatsapp_webhook_payload):
        """Test receiving non-text message through webhook."""
        # Modify payload to have image message instead of text
        sample_whatsapp_webhook_payload["entry"][0]["changes"][0]["value"]["messages"][0] = {
            "from": "1234567890",
            "id": "wamid.test_message_123",
            "timestamp": "1699564800",
            "image": {
                "id": "image_id_123"
            },
            "type": "image"
        }
        
        response = client.post("/api/webhook", json=sample_whatsapp_webhook_payload)
        
        assert response.status_code == 200

    def test_receive_webhook_malformed_payload(self, client):
        """Test receiving malformed webhook payload."""
        malformed_payload = {
            "object": "whatsapp_business_account",
            "entry": []  # Empty entry array
        }
        
        response = client.post("/api/webhook", json=malformed_payload)
        
        assert response.status_code == 200

    def test_receive_webhook_missing_phone_number_id(self, client, sample_whatsapp_webhook_payload):
        """Test webhook with missing phone number ID."""
        # Remove phone_number_id from metadata
        del sample_whatsapp_webhook_payload["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        
        response = client.post("/api/webhook", json=sample_whatsapp_webhook_payload)
        
        assert response.status_code == 200

    @patch('app.api.webhook.get_legal_agent')
    @patch('app.api.webhook.process_legal_query')
    @patch('app.api.webhook.send_whatsapp_reply')
    @patch('app.api.webhook.mark_message_as_read')
    async def test_receive_webhook_agent_error(
        self, 
        mock_mark_read, 
        mock_send_reply, 
        mock_process_query, 
        mock_get_agent,
        client, 
        sample_whatsapp_webhook_payload
    ):
        """Test webhook handling when agent processing fails."""
        # Setup mocks with agent error
        mock_agent = AsyncMock()
        mock_get_agent.return_value = mock_agent
        mock_process_query.side_effect = Exception("Agent processing error")
        mock_send_reply.return_value = AsyncMock()
        mock_mark_read.return_value = AsyncMock()
        
        response = client.post("/api/webhook", json=sample_whatsapp_webhook_payload)
        
        assert response.status_code == 200

    @patch('httpx.AsyncClient')
    async def test_send_whatsapp_reply_success(self, mock_client_class):
        """Test successful WhatsApp reply sending."""
        from app.api.webhook import send_whatsapp_reply
        
        # Mock httpx client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.json.return_value = {"messages": [{"id": "wamid.sent_123"}]}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await send_whatsapp_reply(
            business_phone_number_id="PHONE_NUMBER_ID",
            to="1234567890",
            message_text="Test response",
            reply_to_message_id="wamid.original_123"
        )
        
        assert result is not None
        mock_client.post.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_send_whatsapp_reply_no_reply_id(self, mock_client_class):
        """Test WhatsApp reply sending without reply-to message ID."""
        from app.api.webhook import send_whatsapp_reply
        
        # Mock httpx client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.json.return_value = {"messages": [{"id": "wamid.sent_123"}]}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await send_whatsapp_reply(
            business_phone_number_id="PHONE_NUMBER_ID",
            to="1234567890",
            message_text="Test response"
        )
        
        assert result is not None
        mock_client.post.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_send_whatsapp_reply_http_error(self, mock_client_class):
        """Test WhatsApp reply sending with HTTP error."""
        from app.api.webhook import send_whatsapp_reply
        import httpx
        
        # Mock httpx client to raise HTTP error
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await send_whatsapp_reply(
            business_phone_number_id="PHONE_NUMBER_ID",
            to="1234567890",
            message_text="Test response"
        )
        
        assert result is None

    @patch('httpx.AsyncClient')
    async def test_mark_message_as_read_success(self, mock_client_class):
        """Test successful message read marking."""
        from app.api.webhook import mark_message_as_read
        
        # Mock httpx client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await mark_message_as_read(
            business_phone_number_id="PHONE_NUMBER_ID",
            message_id="wamid.test_123"
        )
        
        assert result is not None
        mock_client.post.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_mark_message_as_read_http_error(self, mock_client_class):
        """Test message read marking with HTTP error."""
        from app.api.webhook import mark_message_as_read
        import httpx
        
        # Mock httpx client to raise HTTP error
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await mark_message_as_read(
            business_phone_number_id="PHONE_NUMBER_ID",
            message_id="wamid.test_123"
        )
        
        assert result is None

    def test_webhook_payload_structure_validation(self, sample_whatsapp_webhook_payload):
        """Test that sample webhook payload has expected structure."""
        payload = sample_whatsapp_webhook_payload
        
        assert "object" in payload
        assert "entry" in payload
        assert len(payload["entry"]) > 0
        
        entry = payload["entry"][0]
        assert "changes" in entry
        assert len(entry["changes"]) > 0
        
        change = entry["changes"][0]
        assert "value" in change
        
        value = change["value"]
        assert "metadata" in value
        assert "messages" in value
        
        message = value["messages"][0]
        assert "from" in message
        assert "id" in message
        assert "type" in message
        assert message["type"] == "text"
        assert "text" in message
        assert "body" in message["text"]