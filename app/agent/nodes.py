"""
LangGraph nodes for the Colombian Labor Law agent workflow.
"""

import os
import logging
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState, add_message_to_history
from .knowledge import identify_legal_topic, get_topic_context
from .prompts import (
    CLASSIFICATION_PROMPT, 
    GREETING_RESPONSE, 
    ERROR_RESPONSE,
    create_legal_prompt,
    create_system_prompt
)

logger = logging.getLogger(__name__)

# Initialize Claude client
def get_claude_client():
    """Initialize Claude client with API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0.1
    )


async def classify_message_node(state: AgentState) -> Dict[str, Any]:
    """
    Classify if the message is a legal question or casual conversation.
    """
    try:
        message = state["current_message"].strip()
        
        # Handle empty messages
        if not message:
            state["is_legal_question"] = False
            state["response"] = "Por favor, envía tu consulta sobre derecho laboral colombiano."
            return state
        
        # Simple heuristics for common greetings
        casual_greetings = ["hola", "oe", "hey", "buenas", "saludos", "hi", "hello"]
        if message.lower() in casual_greetings:
            state["is_legal_question"] = False
            state["response"] = GREETING_RESPONSE
            return state
        
        # Use Claude for more complex classification
        claude = get_claude_client()
        
        classification_prompt = CLASSIFICATION_PROMPT.format(message=message)
        
        response = await claude.ainvoke([HumanMessage(content=classification_prompt)])
        classification = response.content.strip().upper()
        
        state["is_legal_question"] = classification == "LEGAL"
        
        if not state["is_legal_question"]:
            state["response"] = GREETING_RESPONSE
        
        logger.info(f"Message classified as: {classification}")
        
    except Exception as e:
        logger.error(f"Error in classify_message_node: {e}")
        state["error_message"] = str(e)
        state["is_legal_question"] = False
        state["response"] = ERROR_RESPONSE
    
    return state


async def analyze_legal_question_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyze the legal question and identify relevant topics.
    """
    try:
        message = state["current_message"]
        
        # Identify legal topic
        legal_topic = identify_legal_topic(message)
        state["legal_topic"] = legal_topic
        
        # Get relevant legal context
        legal_context = get_topic_context(legal_topic)
        state["legal_context"] = legal_context
        
        logger.info(f"Legal topic identified: {legal_topic}")
        
    except Exception as e:
        logger.error(f"Error in analyze_legal_question_node: {e}")
        state["error_message"] = str(e)
    
    return state


async def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate a legal response using Claude 4.
    """
    try:
        claude = get_claude_client()
        
        # Create system prompt with legal context
        system_prompt = create_system_prompt(
            state.get("legal_context", ""),
            state["conversation_history"]
        )
        
        # Create user prompt
        user_prompt = create_legal_prompt(
            question=state["current_message"],
            legal_topic=state.get("legal_topic", "general"),
            legal_context=state.get("legal_context", ""),
            conversation_history=state["conversation_history"]
        )
        
        # Generate response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await claude.ainvoke(messages)
        generated_response = response.content.strip()
        
        # Ensure response fits WhatsApp limits (roughly 1000 chars)
        if len(generated_response) > 1000:
            generated_response = generated_response[:950] + "..."
        
        state["response"] = generated_response
        state["confidence_score"] = 0.8  # Default confidence
        
        logger.info("Legal response generated successfully")
        
    except Exception as e:
        logger.error(f"Error in generate_response_node: {e}")
        state["error_message"] = str(e)
        state["response"] = ERROR_RESPONSE
        state["confidence_score"] = 0.0
    
    return state


async def ask_followup_node(state: AgentState) -> Dict[str, Any]:
    """
    Add a follow-up question to encourage continued conversation.
    """
    try:
        # Only add followup for legal responses, not for greetings or errors
        if state["is_legal_question"] and not state.get("error_message"):
            followup_question = "\n\n¿Tienes alguna otra pregunta sobre derecho laboral?"
            state["response"] = state["response"] + followup_question
        
        logger.info("Follow-up question added to response")
        
    except Exception as e:
        logger.error(f"Error in ask_followup_node: {e}")
        state["error_message"] = str(e)
    
    return state


async def update_conversation_node(state: AgentState) -> Dict[str, Any]:
    """
    Update conversation history with current interaction.
    """
    try:
        # Add user message to history
        add_message_to_history(
            state, 
            role="user", 
            content=state["current_message"],
            message_id=state["message_id"]
        )
        
        # Add assistant response to history
        add_message_to_history(
            state, 
            role="assistant", 
            content=state["response"]
        )
        
        # Determine if follow-up is needed
        response_lower = state["response"].lower()
        followup_indicators = ["¿", "pregunta", "consulta", "más información"]
        state["requires_followup"] = any(indicator in response_lower for indicator in followup_indicators)
        
        logger.info("Conversation history updated")
        
    except Exception as e:
        logger.error(f"Error in update_conversation_node: {e}")
        state["error_message"] = str(e)
    
    return state


def should_analyze_legal(state: AgentState) -> str:
    """Conditional edge: determine if we should analyze as legal question."""
    if state.get("error_message"):
        return "error"
    return "analyze" if state["is_legal_question"] else "respond"


def should_generate_response(state: AgentState) -> str:
    """Conditional edge: determine if we should generate response."""
    if state.get("error_message"):
        return "error"
    return "generate"


def workflow_complete(state: AgentState) -> str:
    """Final edge: workflow is complete."""
    return "end"
