"""
Agent state management for the Colombian Labor Law assistant.
"""

from typing import Dict, List, Optional, TypedDict
from datetime import datetime


class Message(TypedDict):
    """Represents a single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    message_id: Optional[str]


class AgentState(TypedDict):
    """
    State schema for the Colombian Labor Law agent.
    
    This state is passed between nodes in the LangGraph workflow.
    """
    # User identification
    user_id: str
    phone_number: str
    
    # Current message processing
    current_message: str
    message_id: str
    
    # Conversation context
    conversation_history: List[Message]
    
    # Legal analysis
    legal_topic: Optional[str]  # Identified legal topic
    legal_context: Optional[str]  # Relevant legal information
    
    # Response generation
    response: str
    confidence_score: float  # 0.0 to 1.0
    
    # Workflow control
    requires_followup: bool
    is_legal_question: bool
    error_message: Optional[str]


def create_initial_state(user_id: str, phone_number: str, message: str, message_id: str) -> AgentState:
    """Create initial agent state for a new message."""
    return AgentState(
        user_id=user_id,
        phone_number=phone_number,
        current_message=message,
        message_id=message_id,
        conversation_history=[],
        legal_topic=None,
        legal_context=None,
        response="",
        confidence_score=0.0,
        requires_followup=False,
        is_legal_question=False,
        error_message=None
    )


def add_message_to_history(state: AgentState, role: str, content: str, message_id: Optional[str] = None) -> None:
    """Add a message to the conversation history."""
    message = Message(
        role=role,
        content=content,
        timestamp=datetime.now().isoformat(),
        message_id=message_id
    )
    state["conversation_history"].append(message)


def get_recent_conversation(state: AgentState, max_messages: int = 10) -> List[Message]:
    """Get the most recent messages from conversation history."""
    return state["conversation_history"][-max_messages:]
