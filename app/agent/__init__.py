"""
Colombian Labor Law LangGraph Agent

This module provides an intelligent agent for handling Colombian labor law questions
through WhatsApp integration using LangGraph and Claude 4.
"""

from .workflow import create_legal_agent
from .state import AgentState

__all__ = ["create_legal_agent", "AgentState"]
