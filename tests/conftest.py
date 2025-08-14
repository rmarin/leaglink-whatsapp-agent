import pytest
import os
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.agent.state import AgentState, Message


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_anthropic_api():
    """Mock Anthropic API responses."""
    mock = Mock()
    mock.invoke = AsyncMock(return_value="Mocked Claude response")
    mock.ainvoke = AsyncMock(return_value="Mocked Claude response")
    return mock


@pytest.fixture
def mock_whatsapp_api():
    """Mock WhatsApp Graph API responses."""
    mock = AsyncMock()
    mock.post.return_value.json.return_value = {
        "messaging_product": "whatsapp",
        "to": "1234567890",
        "messages": [{"id": "wamid.mock_message_id"}]
    }
    mock.post.return_value.raise_for_status = Mock()
    return mock


@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing."""
    return AgentState(
        user_id="test_user_123",
        phone_number="1234567890",
        current_message="¿Cuáles son mis derechos laborales?",
        message_id="wamid.test_message_123",
        conversation_history=[],
        legal_topic=None,
        legal_context=None,
        response="",
        confidence_score=0.0,
        requires_followup=False,
        is_legal_question=False,
        error_message=None
    )


@pytest.fixture
def sample_message():
    """Sample message for testing."""
    return Message(
        role="user",
        content="¿Cuáles son mis derechos laborales?",
        timestamp=datetime.now().isoformat(),
        message_id="wamid.test_message_123"
    )


@pytest.fixture
def sample_whatsapp_webhook_payload():
    """Sample WhatsApp webhook payload."""
    return {
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
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "1234567890"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "1234567890",
                                    "id": "wamid.test_message_123",
                                    "timestamp": "1699564800",
                                    "text": {
                                        "body": "¿Cuáles son mis derechos laborales?"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "test_verify_token")
    monkeypatch.setenv("GRAPH_API_TOKEN", "test_graph_api_token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_api_key")


@pytest.fixture
def mock_legal_agent():
    """Mock legal agent for testing."""
    mock_agent = AsyncMock()
    mock_agent.ainvoke = AsyncMock(return_value={
        "response": "Esta es una respuesta simulada del agente legal",
        "legal_topic": "derechos_laborales",
        "confidence_score": 0.85
    })
    return mock_agent


@pytest.fixture(autouse=True)
def setup_test_environment(mock_env_vars):
    """Automatically set up test environment for all tests."""
    pass