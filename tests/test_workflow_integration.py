import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agent.workflow import create_legal_agent, process_legal_query
from app.agent.state import create_initial_state


@pytest.mark.asyncio
async def test_end_to_end_workflow_integration():
    """Test complete workflow integration from message input to response generation."""
    
    # Mock Claude client response
    mock_response = Mock()
    mock_response.content = "Sus derechos laborales incluyen: salario mínimo, vacaciones, prestaciones sociales, y protección contra despido injustificado."
    
    mock_claude_client = AsyncMock()
    mock_claude_client.ainvoke.return_value = mock_response
    
    with patch('app.agent.nodes.get_claude_client', return_value=mock_claude_client):
        # Test input
        user_id = "test_user_123"
        phone_number = "573001234567"
        message = "¿Cuáles son mis derechos laborales?"
        message_id = "msg_test_123"
        
        # Create and run workflow
        agent = create_legal_agent()
        response = await process_legal_query(
            agent=agent,
            user_id=user_id,
            phone_number=phone_number, 
            message=message,
            message_id=message_id
        )
        
        # Verify response
        assert response is not None
        assert len(response) > 0
        assert "derecho" in response.lower() or "laboral" in response.lower()
        assert response != "Lo siento, no pude procesar tu consulta."
        
        # Verify Claude client was called
        mock_claude_client.ainvoke.assert_called()
        
        # Verify we got a meaningful legal response (not just error message)
        assert "problema técnico" not in response