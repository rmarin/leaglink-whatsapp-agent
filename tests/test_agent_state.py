import pytest
from datetime import datetime
from app.agent.state import (
    AgentState,
    Message,
    create_initial_state,
    add_message_to_history,
    get_recent_conversation
)


@pytest.mark.unit
class TestAgentState:
    """Test cases for agent state management."""

    def test_create_initial_state(self):
        """Test creating initial agent state."""
        user_id = "test_user_123"
        phone_number = "1234567890"
        message = "¿Cuáles son mis derechos laborales?"
        message_id = "wamid.test_message_123"

        state = create_initial_state(user_id, phone_number, message, message_id)

        assert state["user_id"] == user_id
        assert state["phone_number"] == phone_number
        assert state["current_message"] == message
        assert state["message_id"] == message_id
        assert state["conversation_history"] == []
        assert state["legal_topic"] is None
        assert state["legal_context"] is None
        assert state["response"] == ""
        assert state["confidence_score"] == 0.0
        assert state["requires_followup"] is False
        assert state["is_legal_question"] is False
        assert state["error_message"] is None

    def test_add_message_to_history_user_message(self, sample_agent_state):
        """Test adding a user message to conversation history."""
        content = "Test user message"
        message_id = "wamid.test_123"
        
        add_message_to_history(sample_agent_state, "user", content, message_id)
        
        assert len(sample_agent_state["conversation_history"]) == 1
        message = sample_agent_state["conversation_history"][0]
        assert message["role"] == "user"
        assert message["content"] == content
        assert message["message_id"] == message_id
        assert "timestamp" in message

    def test_add_message_to_history_assistant_message(self, sample_agent_state):
        """Test adding an assistant message to conversation history."""
        content = "Test assistant response"
        
        add_message_to_history(sample_agent_state, "assistant", content)
        
        assert len(sample_agent_state["conversation_history"]) == 1
        message = sample_agent_state["conversation_history"][0]
        assert message["role"] == "assistant"
        assert message["content"] == content
        assert message["message_id"] is None
        assert "timestamp" in message

    def test_add_multiple_messages_to_history(self, sample_agent_state):
        """Test adding multiple messages to conversation history."""
        add_message_to_history(sample_agent_state, "user", "First message", "msg_1")
        add_message_to_history(sample_agent_state, "assistant", "First response")
        add_message_to_history(sample_agent_state, "user", "Second message", "msg_2")
        
        assert len(sample_agent_state["conversation_history"]) == 3
        assert sample_agent_state["conversation_history"][0]["role"] == "user"
        assert sample_agent_state["conversation_history"][1]["role"] == "assistant"
        assert sample_agent_state["conversation_history"][2]["role"] == "user"

    def test_get_recent_conversation_within_limit(self, sample_agent_state):
        """Test getting recent conversation within the message limit."""
        # Add 5 messages
        for i in range(5):
            add_message_to_history(sample_agent_state, "user", f"Message {i}", f"msg_{i}")
        
        recent_messages = get_recent_conversation(sample_agent_state, max_messages=3)
        
        assert len(recent_messages) == 3
        assert recent_messages[0]["content"] == "Message 2"  # Last 3 messages
        assert recent_messages[1]["content"] == "Message 3"
        assert recent_messages[2]["content"] == "Message 4"

    def test_get_recent_conversation_all_messages(self, sample_agent_state):
        """Test getting recent conversation when total messages is less than limit."""
        # Add 3 messages
        for i in range(3):
            add_message_to_history(sample_agent_state, "user", f"Message {i}", f"msg_{i}")
        
        recent_messages = get_recent_conversation(sample_agent_state, max_messages=10)
        
        assert len(recent_messages) == 3
        assert recent_messages[0]["content"] == "Message 0"
        assert recent_messages[1]["content"] == "Message 1"
        assert recent_messages[2]["content"] == "Message 2"

    def test_get_recent_conversation_empty_history(self, sample_agent_state):
        """Test getting recent conversation with empty history."""
        recent_messages = get_recent_conversation(sample_agent_state, max_messages=5)
        
        assert len(recent_messages) == 0
        assert recent_messages == []

    def test_message_timestamp_format(self, sample_agent_state):
        """Test that message timestamps are in ISO format."""
        add_message_to_history(sample_agent_state, "user", "Test message", "msg_1")
        
        message = sample_agent_state["conversation_history"][0]
        timestamp = message["timestamp"]
        
        # Try to parse timestamp - will raise exception if invalid format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_agent_state_type_annotations(self):
        """Test that AgentState maintains proper type structure."""
        state = create_initial_state("user", "phone", "message", "msg_id")
        
        # Check types
        assert isinstance(state["user_id"], str)
        assert isinstance(state["phone_number"], str)
        assert isinstance(state["current_message"], str)
        assert isinstance(state["message_id"], str)
        assert isinstance(state["conversation_history"], list)
        assert isinstance(state["confidence_score"], (int, float))
        assert isinstance(state["requires_followup"], bool)
        assert isinstance(state["is_legal_question"], bool)