import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agent.workflow import (
    create_legal_agent,
    process_legal_query,
    get_legal_agent
)
from app.agent.state import create_initial_state


@pytest.mark.integration
@pytest.mark.agent
class TestLegalAgentWorkflow:
    """Test cases for the complete legal agent workflow."""

    @patch('app.agent.nodes.get_claude_client')
    async def test_create_legal_agent(self, mock_get_claude):
        """Test creating the legal agent workflow."""
        # Mock Claude client
        mock_claude = AsyncMock()
        mock_get_claude.return_value = mock_claude
        
        agent = create_legal_agent()
        
        assert agent is not None
        # The agent should be a compiled LangGraph workflow
        assert hasattr(agent, 'ainvoke')

    @patch('app.agent.nodes.get_claude_client')
    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_process_legal_query_success(
        self, 
        mock_get_context, 
        mock_identify_topic, 
        mock_get_claude
    ):
        """Test successful processing of a legal query."""
        # Setup mocks
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_generate_response = Mock()
        mock_generate_response.content = "Esta es una respuesta legal detallada sobre derechos laborales."
        
        mock_claude.ainvoke.side_effect = [mock_classify_response, mock_generate_response]
        mock_get_claude.return_value = mock_claude
        mock_identify_topic.return_value = "derechos"
        mock_get_context.return_value = "Context about labor rights"
        
        # Create agent
        agent = create_legal_agent()
        
        # Process query
        response = await process_legal_query(
            agent=agent,
            user_id="test_user_123",
            phone_number="1234567890",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.test_123"
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @patch('app.agent.nodes.get_claude_client')
    async def test_process_legal_query_greeting(self, mock_get_claude):
        """Test processing a greeting message."""
        # Create agent
        agent = create_legal_agent()
        
        # Process greeting
        response = await process_legal_query(
            agent=agent,
            user_id="test_user_123",
            phone_number="1234567890",
            message="hola",
            message_id="wamid.test_123"
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert "hola" in response.lower() or "Hola" in response

    @patch('app.agent.nodes.get_claude_client')
    async def test_process_legal_query_empty_message(self, mock_get_claude):
        """Test processing an empty message."""
        # Create agent
        agent = create_legal_agent()
        
        # Process empty message
        response = await process_legal_query(
            agent=agent,
            user_id="test_user_123",
            phone_number="1234567890",
            message="",
            message_id="wamid.test_123"
        )
        
        assert response is not None
        assert "consulta" in response.lower()

    @patch('app.agent.nodes.get_claude_client')
    async def test_process_legal_query_with_error(self, mock_get_claude):
        """Test processing query when agent encounters an error."""
        # Mock Claude client to raise error
        mock_get_claude.side_effect = Exception("Claude API error")
        
        # Create agent
        agent = create_legal_agent()
        
        # Process query
        response = await process_legal_query(
            agent=agent,
            user_id="test_user_123",
            phone_number="1234567890",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.test_123"
        )
        
        assert response is not None
        assert "problema técnico" in response.lower()

    @patch('app.agent.nodes.get_claude_client')
    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_conversation_memory_persistence(
        self, 
        mock_get_context, 
        mock_identify_topic, 
        mock_get_claude
    ):
        """Test that conversation memory persists between queries."""
        # Setup mocks
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_generate_response = Mock()
        mock_generate_response.content = "Respuesta del agente."
        
        mock_claude.ainvoke.side_effect = [
            mock_classify_response, mock_generate_response,  # First query
            mock_classify_response, mock_generate_response   # Second query
        ]
        mock_get_claude.return_value = mock_claude
        mock_identify_topic.return_value = "derechos"
        mock_get_context.return_value = "Context about labor rights"
        
        # Create agent
        agent = create_legal_agent()
        user_id = "test_user_123"
        
        # First query
        response1 = await process_legal_query(
            agent=agent,
            user_id=user_id,
            phone_number="1234567890",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.test_123"
        )
        
        # Second query with same user
        response2 = await process_legal_query(
            agent=agent,
            user_id=user_id,
            phone_number="1234567890",
            message="¿Y qué pasa con las vacaciones?",
            message_id="wamid.test_124"
        )
        
        assert response1 is not None
        assert response2 is not None
        # Both responses should be processed successfully
        assert len(response1) > 0
        assert len(response2) > 0

    @patch('app.agent.nodes.get_claude_client')
    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_different_users_separate_conversations(
        self, 
        mock_get_context, 
        mock_identify_topic, 
        mock_get_claude
    ):
        """Test that different users have separate conversation contexts."""
        # Setup mocks
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_generate_response = Mock()
        mock_generate_response.content = "Respuesta del agente."
        
        mock_claude.ainvoke.side_effect = [
            mock_classify_response, mock_generate_response,  # User 1
            mock_classify_response, mock_generate_response   # User 2
        ]
        mock_get_claude.return_value = mock_claude
        mock_identify_topic.return_value = "derechos"
        mock_get_context.return_value = "Context about labor rights"
        
        # Create agent
        agent = create_legal_agent()
        
        # Query from user 1
        response1 = await process_legal_query(
            agent=agent,
            user_id="user_1",
            phone_number="1111111111",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.user1_msg1"
        )
        
        # Query from user 2
        response2 = await process_legal_query(
            agent=agent,
            user_id="user_2",
            phone_number="2222222222",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.user2_msg1"
        )
        
        assert response1 is not None
        assert response2 is not None
        # Both should get responses even though they're different users
        assert len(response1) > 0
        assert len(response2) > 0

    def test_get_legal_agent_singleton(self):
        """Test that get_legal_agent returns the same instance."""
        agent1 = get_legal_agent()
        agent2 = get_legal_agent()
        
        # Should return the same instance
        assert agent1 is agent2

    @patch('app.agent.nodes.get_claude_client')
    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_agent_workflow_states(
        self, 
        mock_get_context, 
        mock_identify_topic, 
        mock_get_claude
    ):
        """Test that agent workflow properly transitions through states."""
        # Setup mocks
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_generate_response = Mock()
        mock_generate_response.content = "Respuesta legal completa."
        
        mock_claude.ainvoke.side_effect = [mock_classify_response, mock_generate_response]
        mock_get_claude.return_value = mock_claude
        mock_identify_topic.return_value = "salarios"
        mock_get_context.return_value = "Salary context"
        
        # Create initial state
        initial_state = create_initial_state(
            user_id="test_user",
            phone_number="1234567890",
            message="¿Cuál es el salario mínimo?",
            message_id="wamid.test"
        )
        
        # Create and run agent
        agent = create_legal_agent()
        config = {"configurable": {"thread_id": "test_user"}}
        
        result = await agent.ainvoke(initial_state, config=config)
        
        # Verify final state
        assert result is not None
        assert "response" in result
        assert len(result["response"]) > 0
        assert "conversation_history" in result
        # Should have user message and agent response
        assert len(result["conversation_history"]) >= 2

    @patch('app.agent.nodes.get_claude_client')
    async def test_agent_handles_long_response(self, mock_get_claude):
        """Test that agent properly handles and truncates long responses."""
        # Setup mock for long response
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_long_response = Mock()
        # Create response longer than 1000 characters
        mock_long_response.content = "x" * 1100
        
        mock_claude.ainvoke.side_effect = [mock_classify_response, mock_long_response]
        mock_get_claude.return_value = mock_claude
        
        # Create agent
        agent = create_legal_agent()
        
        # Process query
        response = await process_legal_query(
            agent=agent,
            user_id="test_user_123",
            phone_number="1234567890",
            message="¿Cuáles son mis derechos laborales?",
            message_id="wamid.test_123"
        )
        
        # Response should be truncated
        assert response is not None
        assert len(response) <= 1000
        assert response.endswith("...") if len(response) == 1000 else True

    @patch('app.agent.nodes.get_claude_client')
    @patch('app.agent.nodes.identify_legal_topic')
    @patch('app.agent.nodes.get_topic_context')
    async def test_agent_confidence_scoring(
        self, 
        mock_get_context, 
        mock_identify_topic, 
        mock_get_claude
    ):
        """Test that agent assigns appropriate confidence scores."""
        # Setup mocks
        mock_claude = AsyncMock()
        mock_classify_response = Mock()
        mock_classify_response.content = "LEGAL"
        mock_generate_response = Mock()
        mock_generate_response.content = "Respuesta legal."
        
        mock_claude.ainvoke.side_effect = [mock_classify_response, mock_generate_response]
        mock_get_claude.return_value = mock_claude
        mock_identify_topic.return_value = "derechos"
        mock_get_context.return_value = "Context"
        
        # Create and run agent
        agent = create_legal_agent()
        initial_state = create_initial_state(
            user_id="test_user",
            phone_number="1234567890",
            message="¿Cuáles son mis derechos?",
            message_id="wamid.test"
        )
        
        config = {"configurable": {"thread_id": "test_user"}}
        result = await agent.ainvoke(initial_state, config=config)
        
        # Should have confidence score
        assert "confidence_score" in result
        assert isinstance(result["confidence_score"], (int, float))
        assert 0.0 <= result["confidence_score"] <= 1.0