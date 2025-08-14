import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agent.nodes import (
    classify_message_node,
    analyze_legal_question_node,
    generate_response_node,
    update_conversation_node,
    should_analyze_legal,
    should_generate_response,
    workflow_complete,
    get_claude_client
)
from app.agent.state import create_initial_state


@pytest.mark.unit
@pytest.mark.agent
class TestAgentNodes:
    """Test cases for agent workflow nodes."""

    async def test_classify_message_node_empty_message(self, sample_agent_state):
        """Test classify_message_node with empty message."""
        sample_agent_state["current_message"] = ""
        
        result = await classify_message_node(sample_agent_state)
        
        assert result["is_legal_question"] is False
        assert "Por favor, envía tu consulta" in result["response"]

    async def test_classify_message_node_greeting(self, sample_agent_state):
        """Test classify_message_node with greeting message."""
        sample_agent_state["current_message"] = "hola"
        
        result = await classify_message_node(sample_agent_state)
        
        assert result["is_legal_question"] is False
        assert "Hola" in result["response"] or "hola" in result["response"].lower()

    @patch('app.agent.nodes.get_claude_client')
    async def test_classify_message_node_legal_question(self, mock_get_claude, sample_agent_state):
        """Test classify_message_node with legal question."""
        sample_agent_state["current_message"] = "¿Cuáles son mis derechos laborales?"
        
        # Mock Claude response
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = "LEGAL"
        mock_claude.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_claude.return_value = mock_claude
        
        result = await classify_message_node(sample_agent_state)
        
        assert result["is_legal_question"] is True
        mock_claude.ainvoke.assert_called_once()

    @patch('app.agent.nodes.get_claude_client')
    async def test_classify_message_node_non_legal(self, mock_get_claude, sample_agent_state):
        """Test classify_message_node with non-legal message."""
        sample_agent_state["current_message"] = "¿Cómo está el clima?"
        
        # Mock Claude response
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = "CASUAL"
        mock_claude.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_claude.return_value = mock_claude
        
        result = await classify_message_node(sample_agent_state)
        
        assert result["is_legal_question"] is False

    @patch('app.agent.nodes.get_claude_client')
    async def test_classify_message_node_error_handling(self, mock_get_claude, sample_agent_state):
        """Test classify_message_node error handling."""
        sample_agent_state["current_message"] = "test message"
        
        # Mock Claude to raise exception
        mock_get_claude.side_effect = Exception("API Error")
        
        result = await classify_message_node(sample_agent_state)
        
        assert result["is_legal_question"] is False
        assert result["error_message"] is not None
        assert "Lo siento" in result["response"]

    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_analyze_legal_question_node(self, mock_get_context, mock_identify, sample_agent_state):
        """Test analyze_legal_question_node."""
        mock_identify.return_value = "derechos_laborales"
        mock_get_context.return_value = "Context about labor rights"
        
        result = await analyze_legal_question_node(sample_agent_state)
        
        assert result["legal_topic"] == "derechos_laborales"
        assert result["legal_context"] == "Context about labor rights"
        mock_identify.assert_called_once_with(sample_agent_state["current_message"])
        mock_get_context.assert_called_once_with("derechos_laborales")

    @patch('app.agent.nodes.identify_legal_topic')
    async def test_analyze_legal_question_node_error(self, mock_identify, sample_agent_state):
        """Test analyze_legal_question_node error handling."""
        mock_identify.side_effect = Exception("Knowledge base error")
        
        result = await analyze_legal_question_node(sample_agent_state)
        
        assert result["error_message"] is not None

    @patch('app.agent.nodes.get_claude_client')
    async def test_generate_response_node_success(self, mock_get_claude, sample_agent_state):
        """Test generate_response_node successful response generation."""
        sample_agent_state["legal_topic"] = "derechos_laborales"
        sample_agent_state["legal_context"] = "Labor rights context"
        
        # Mock Claude response
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Esta es una respuesta legal completa."
        mock_claude.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_claude.return_value = mock_claude
        
        result = await generate_response_node(sample_agent_state)
        
        assert result["response"] == "Esta es una respuesta legal completa."
        assert result["confidence_score"] == 0.8
        mock_claude.ainvoke.assert_called_once()

    @patch('app.agent.nodes.get_claude_client')
    async def test_generate_response_node_long_response(self, mock_get_claude, sample_agent_state):
        """Test generate_response_node with long response truncation."""
        # Mock very long response
        long_response = "x" * 1100  # Longer than 1000 chars
        
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = long_response
        mock_claude.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_claude.return_value = mock_claude
        
        result = await generate_response_node(sample_agent_state)
        
        assert len(result["response"]) <= 1000
        assert result["response"].endswith("...")

    @patch('app.agent.nodes.get_claude_client')
    async def test_generate_response_node_error(self, mock_get_claude, sample_agent_state):
        """Test generate_response_node error handling."""
        mock_get_claude.side_effect = Exception("Claude API error")
        
        result = await generate_response_node(sample_agent_state)
        
        assert result["error_message"] is not None
        assert "Lo siento" in result["response"]
        assert result["confidence_score"] == 0.0

    async def test_update_conversation_node(self, sample_agent_state):
        """Test update_conversation_node adds messages to history."""
        sample_agent_state["response"] = "Esta es la respuesta del agente."
        
        result = await update_conversation_node(sample_agent_state)
        
        assert len(result["conversation_history"]) == 2
        assert result["conversation_history"][0]["role"] == "user"
        assert result["conversation_history"][0]["content"] == sample_agent_state["current_message"]
        assert result["conversation_history"][1]["role"] == "assistant"
        assert result["conversation_history"][1]["content"] == "Esta es la respuesta del agente."

    async def test_update_conversation_node_followup_detection(self, sample_agent_state):
        """Test update_conversation_node detects follow-up requirements."""
        sample_agent_state["response"] = "¿Tienes alguna otra pregunta?"
        
        result = await update_conversation_node(sample_agent_state)
        
        assert result["requires_followup"] is True

    async def test_update_conversation_node_no_followup(self, sample_agent_state):
        """Test update_conversation_node when no follow-up is needed."""
        sample_agent_state["response"] = "Esta es la respuesta completa."
        
        result = await update_conversation_node(sample_agent_state)
        
        assert result["requires_followup"] is False

    def test_should_analyze_legal_with_legal_question(self, sample_agent_state):
        """Test should_analyze_legal conditional edge with legal question."""
        sample_agent_state["is_legal_question"] = True
        
        result = should_analyze_legal(sample_agent_state)
        
        assert result == "analyze"

    def test_should_analyze_legal_with_non_legal(self, sample_agent_state):
        """Test should_analyze_legal conditional edge with non-legal message."""
        sample_agent_state["is_legal_question"] = False
        
        result = should_analyze_legal(sample_agent_state)
        
        assert result == "respond"

    def test_should_analyze_legal_with_error(self, sample_agent_state):
        """Test should_analyze_legal conditional edge with error."""
        sample_agent_state["error_message"] = "Some error"
        sample_agent_state["is_legal_question"] = True
        
        result = should_analyze_legal(sample_agent_state)
        
        assert result == "error"

    def test_should_generate_response_success(self, sample_agent_state):
        """Test should_generate_response conditional edge without error."""
        result = should_generate_response(sample_agent_state)
        
        assert result == "generate"

    def test_should_generate_response_with_error(self, sample_agent_state):
        """Test should_generate_response conditional edge with error."""
        sample_agent_state["error_message"] = "Some error"
        
        result = should_generate_response(sample_agent_state)
        
        assert result == "error"

    def test_workflow_complete(self, sample_agent_state):
        """Test workflow_complete always returns end."""
        result = workflow_complete(sample_agent_state)
        
        assert result == "end"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_get_claude_client_success(self):
        """Test get_claude_client with valid API key."""
        client = get_claude_client()
        
        assert client is not None
        assert hasattr(client, 'model')

    @patch.dict('os.environ', {}, clear=True)
    def test_get_claude_client_missing_key(self):
        """Test get_claude_client without API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
            get_claude_client()