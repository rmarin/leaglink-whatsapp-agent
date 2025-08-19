import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import json

from app.agent.state import AgentState, Message, create_initial_state, add_message_to_history, get_recent_conversation
from app.agent.knowledge import identify_legal_topic, get_topic_context, LEGAL_TOPICS
from app.agent.prompts import format_conversation_history, create_legal_prompt, create_system_prompt
from app.agent.workflow import process_legal_query


@pytest.mark.comprehensive 
class TestLegalAgentComprehensive:
    """Comprehensive tests for the Colombian Labor Law agent system - Updated version."""

    def test_agent_state_creation_and_management(self):
        """Test agent state creation and conversation management."""
        # Test initial state creation
        state = create_initial_state(
            user_id="test_user_123",
            phone_number="573001234567", 
            message="¿Cuáles son mis derechos laborales?",
            message_id="msg_123"
        )
        
        # Verify initial state structure
        assert state["user_id"] == "test_user_123"
        assert state["phone_number"] == "573001234567"
        assert state["current_message"] == "¿Cuáles son mis derechos laborales?"
        assert state["message_id"] == "msg_123"
        assert state["conversation_history"] == []
        assert state["legal_topic"] is None
        assert state["response"] == ""
        assert state["confidence_score"] == 0.0
        assert state["requires_followup"] is False
        assert state["is_legal_question"] is False
        assert state["error_message"] is None

    def test_conversation_history_management(self):
        """Test adding messages and retrieving conversation history."""
        state = create_initial_state("user1", "123456789", "test", "msg1")
        
        # Add user message
        add_message_to_history(state, "user", "¿Cuántos días de vacaciones tengo?", "msg1")
        
        # Add assistant response
        add_message_to_history(state, "assistant", "Tienes 15 días hábiles de vacaciones por año.")
        
        # Verify conversation history
        assert len(state["conversation_history"]) == 2
        assert state["conversation_history"][0]["role"] == "user"
        assert state["conversation_history"][0]["content"] == "¿Cuántos días de vacaciones tengo?"
        assert state["conversation_history"][1]["role"] == "assistant"
        
        # Test get_recent_conversation
        recent = get_recent_conversation(state, max_messages=1)
        assert len(recent) == 1
        assert recent[0]["role"] == "assistant"

    def test_legal_topic_identification(self):
        """Test legal topic identification from user messages."""
        # Test contract topics
        contract_msg = "Necesito información sobre mi contrato de trabajo"
        topic = identify_legal_topic(contract_msg)
        assert topic == "contratos"
        
        # Test salary topics
        salary_msg = "¿Cuánto es el salario mínimo en Colombia?"
        topic = identify_legal_topic(salary_msg)
        assert topic == "salarios"
        
        # Test benefits topics
        benefits_msg = "¿Cuándo me pagan las cesantías?"
        topic = identify_legal_topic(benefits_msg)
        assert topic == "prestaciones"
        
        # Test termination topics - use keyword that exists in LEGAL_TOPICS
        termination_msg = "¿Qué pasa cuando hay un despido?"
        topic = identify_legal_topic(termination_msg)
        assert topic == "terminacion"
        
        # Test general topics
        general_msg = "Tengo dudas sobre mis derechos"
        topic = identify_legal_topic(general_msg)
        assert topic == "derechos"
        
        # Test unrelated message
        unrelated_msg = "Hola, ¿cómo estás?"
        topic = identify_legal_topic(unrelated_msg)
        assert topic == "general"

    def test_legal_context_retrieval(self):
        """Test retrieval of legal context for different topics."""
        # Test general context
        general_context = get_topic_context("general")
        assert "INFORMACIÓN BÁSICA DEL DERECHO LABORAL COLOMBIANO" in general_context
        assert "VACACIONES" in general_context
        assert "SALARIO MÍNIMO" in general_context
        
        # Test specific topic context
        contract_context = get_topic_context("contratos")
        assert "INFORMACIÓN BÁSICA DEL DERECHO LABORAL COLOMBIANO" in contract_context
        assert "TEMA ESPECÍFICO: Contratos de trabajo y vinculación laboral" in contract_context

    def test_prompt_formatting(self):
        """Test prompt creation and conversation history formatting."""
        # Create sample conversation history
        messages = [
            {"role": "user", "content": "¿Cuántos días de vacaciones tengo?"},
            {"role": "assistant", "content": "Tienes 15 días hábiles por año."},
            {"role": "user", "content": "¿Y las prestaciones?"}
        ]
        
        # Test conversation history formatting
        formatted = format_conversation_history(messages)
        assert "Usuario: ¿Cuántos días de vacaciones tengo?" in formatted
        assert "Asistente: Tienes 15 días hábiles por año." in formatted
        assert "Usuario: ¿Y las prestaciones?" in formatted
        
        # Test legal prompt creation
        legal_prompt = create_legal_prompt(
            question="¿Cuáles son mis derechos laborales?",
            legal_topic="derechos",
            legal_context="Contexto legal básico",
            conversation_history=messages
        )
        assert "¿Cuáles son mis derechos laborales?" in legal_prompt
        assert "derechos" in legal_prompt
        assert "Contexto legal básico" in legal_prompt
        
        # Test system prompt creation
        system_prompt = create_system_prompt("Contexto legal", messages)
        assert "Contexto legal" in system_prompt
        assert "Usuario: ¿Cuántos días de vacaciones tengo?" in system_prompt

    def test_webhook_payload_processing(self, sample_whatsapp_webhook_payload):
        """Test processing of WhatsApp webhook payload structure."""
        payload = sample_whatsapp_webhook_payload
        
        # Extract message data (simulating webhook processing logic)
        try:
            message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
            business_phone_id = payload["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
            contact = payload["entry"][0]["changes"][0]["value"]["contacts"][0]
        except (IndexError, KeyError):
            pytest.fail("Failed to extract message data from webhook payload")
        
        # Verify extracted data
        assert message["from"] == "1234567890"
        assert message["id"] == "wamid.test_message_123"
        assert message["text"]["body"] == "¿Cuáles son mis derechos laborales?"
        assert message["type"] == "text"
        assert business_phone_id == "PHONE_NUMBER_ID"
        assert contact["wa_id"] == "1234567890"

    @patch('app.agent.nodes.get_claude_client')
    async def test_workflow_integration_mock(self, mock_claude_client):
        """Test workflow integration with mocked Claude client."""
        # Setup mock Claude client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = "LEGAL"
        mock_client.ainvoke.return_value = mock_response
        mock_claude_client.return_value = mock_client
        
        # Create test state
        state = create_initial_state(
            user_id="test_user",
            phone_number="573001234567",
            message="¿Cuáles son mis derechos laborales?",
            message_id="msg_123"
        )
        
        # Test classification node
        from app.agent.nodes import classify_message_node
        result_state = await classify_message_node(state)
        
        # Verify classification
        assert result_state["is_legal_question"] is True
        mock_client.ainvoke.assert_called_once()

    def test_legal_knowledge_base_completeness(self):
        """Test that the legal knowledge base contains expected topics."""
        expected_topics = [
            "contratos", "salarios", "prestaciones", 
            "terminacion", "derechos", "licencias", "seguridad_social"
        ]
        
        for topic in expected_topics:
            assert topic in LEGAL_TOPICS
            assert "keywords" in LEGAL_TOPICS[topic]
            assert "description" in LEGAL_TOPICS[topic]
            assert len(LEGAL_TOPICS[topic]["keywords"]) > 0

    def test_api_message_model_validation(self):
        """Test API message models validation."""
        from app.api.messages import MessageCreate, Message
        from datetime import datetime
        import uuid
        
        # Test message creation
        message_data = {
            "content": "¿Cuáles son mis derechos laborales?",
            "sender": "573001234567"
        }
        
        message_create = MessageCreate(**message_data)
        assert message_create.content == "¿Cuáles son mis derechos laborales?"
        assert message_create.sender == "573001234567"
        
        # Test full message model
        full_message_data = {
            "id": str(uuid.uuid4()),
            "content": "¿Cuáles son mis derechos laborales?", 
            "sender": "573001234567",
            "timestamp": datetime.now()
        }
        
        message = Message(**full_message_data)
        assert message.content == "¿Cuáles son mis derechos laborales?"
        assert message.sender == "573001234567"
        assert isinstance(message.timestamp, datetime)

    def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        # Test empty message handling
        empty_state = create_initial_state("user1", "123", "", "msg1")
        assert empty_state["current_message"] == ""
        
        # Test invalid topic context
        invalid_context = get_topic_context("nonexistent_topic")
        assert "INFORMACIÓN BÁSICA DEL DERECHO LABORAL COLOMBIANO" in invalid_context
        
        # Test empty conversation history
        empty_history = format_conversation_history([])
        assert empty_history == "No hay historial previo."

    async def test_messages_api_endpoints(self, client):
        """Test the messages API endpoints functionality."""
        # Test creating a message
        message_data = {
            "content": "¿Cuáles son mis derechos laborales?",
            "sender": "573001234567"
        }
        
        response = client.post("/api/messages", json=message_data)
        assert response.status_code == 201
        
        created_message = response.json()
        assert created_message["content"] == message_data["content"]
        assert created_message["sender"] == message_data["sender"]
        assert "id" in created_message
        assert "timestamp" in created_message
        
        # Test getting all messages
        response = client.get("/api/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        
        # Test getting specific message
        message_id = created_message["id"]
        response = client.get(f"/api/messages/{message_id}")
        assert response.status_code == 200
        retrieved_message = response.json()
        assert retrieved_message["id"] == message_id
        
        # Test getting non-existent message
        response = client.get("/api/messages/nonexistent-id")
        assert response.status_code == 404

    @patch('app.api.webhook.WEBHOOK_VERIFY_TOKEN', 'test_verify_token')
    def test_webhook_verification(self, client):
        """Test webhook verification endpoint."""
        # Test successful verification
        response = client.get(
            "/api/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "test_challenge_123"
            }
        )
        assert response.status_code == 200
        assert response.text == "test_challenge_123"
        
        # Test failed verification with wrong token
        response = client.get(
            "/api/webhook", 
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "test_challenge_123"
            }
        )
        assert response.status_code == 403

    def test_colombian_labor_law_constants(self):
        """Test that Colombian labor law constants are properly defined."""
        from app.agent.knowledge import LABOR_LAW_BASICS
        
        # Check that basic law information includes key Colombian specifics
        assert "1.300.000" in LABOR_LAW_BASICS  # 2024 minimum wage
        assert "162.000" in LABOR_LAW_BASICS   # Transport allowance
        assert "15 días" in LABOR_LAW_BASICS   # Vacation days
        assert "18 semanas" in LABOR_LAW_BASICS # Maternity leave
        assert "48 horas" in LABOR_LAW_BASICS  # Weekly work hours
        assert "cesantías" in LABOR_LAW_BASICS.lower()
        assert "prima" in LABOR_LAW_BASICS.lower()
        
        # Additional validation for labor rights coverage
        assert "indemnización" in LABOR_LAW_BASICS.lower()
        assert "jornada" in LABOR_LAW_BASICS.lower()

    @pytest.mark.asyncio
    async def test_edge_cases_and_boundaries(self):
        """Test edge cases and boundary conditions."""
        # Test very long message (should be handled gracefully)
        long_message = "¿" + "Cuáles son mis derechos laborales? " * 100
        topic = identify_legal_topic(long_message)
        assert topic == "derechos"
        
        # Test message with special characters
        special_msg = "¿Cuáles son mis derechos laborales? ñáéíóú @#$%"
        topic = identify_legal_topic(special_msg)
        assert topic == "derechos"
        
        # Test case sensitivity
        upper_msg = "CONTRATO DE TRABAJO"
        topic = identify_legal_topic(upper_msg)
        assert topic == "contratos"