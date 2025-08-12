"""
LangGraph workflow definition for the Colombian Labor Law agent.
"""

import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    classify_message_node,
    analyze_legal_question_node,
    generate_response_node,
    update_conversation_node,
    should_analyze_legal,
    should_generate_response,
    workflow_complete
)

logger = logging.getLogger(__name__)


def create_legal_agent():
    """
    Create and configure the LangGraph workflow for legal assistance.
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify", classify_message_node)
    workflow.add_node("analyze", analyze_legal_question_node)
    workflow.add_node("generate", generate_response_node)
    workflow.add_node("update", update_conversation_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "classify",
        should_analyze_legal,
        {
            "analyze": "analyze",
            "respond": "update",
            "error": "update"
        }
    )
    
    workflow.add_conditional_edges(
        "analyze",
        should_generate_response,
        {
            "generate": "generate",
            "error": "update"
        }
    )
    
    # Add regular edges
    workflow.add_edge("generate", "update")
    workflow.add_edge("update", END)
    
    # Add memory for conversation persistence
    memory = MemorySaver()
    
    # Compile the workflow
    app = workflow.compile(checkpointer=memory)
    
    logger.info("Legal agent workflow created successfully")
    
    return app


async def process_legal_query(agent, user_id: str, phone_number: str, message: str, message_id: str) -> str:
    """
    Process a legal query through the agent workflow.
    
    Args:
        agent: Compiled LangGraph agent
        user_id: WhatsApp user ID
        phone_number: User's phone number
        message: User's message
        message_id: WhatsApp message ID
    
    Returns:
        Generated response string
    """
    try:
        from .state import create_initial_state
        
        # Create initial state
        initial_state = create_initial_state(user_id, phone_number, message, message_id)
        
        # Configure thread for conversation persistence
        config = {"configurable": {"thread_id": user_id}}
        
        # Run the workflow
        result = await agent.ainvoke(initial_state, config=config)
        
        # Extract response
        response = result.get("response", "Lo siento, no pude procesar tu consulta.")
        
        logger.info(f"Legal query processed successfully for user {user_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing legal query: {e}")
        return "Lo siento, he tenido un problema técnico. Por favor, intenta de nuevo o contacta con un abogado si es urgente."


# Global agent instance (will be initialized when needed)
_legal_agent = None


def get_legal_agent():
    """Get or create the global legal agent instance."""
    global _legal_agent
    if _legal_agent is None:
        _legal_agent = create_legal_agent()
    return _legal_agent
