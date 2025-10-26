"""
Multi-Agent System for Alto - Financial Assistant

This module implements a multi-agent system using Google ADK's
Coordinator/Dispatcher pattern for intelligent request routing.
"""
from app.agents.calendar_agent import create_calendar_agent
from app.agents.coordinator_agent import create_coordinator_agent
from app.agents.qa_agent import create_qa_agent

__all__ = [
    "create_calendar_agent",
    "create_qa_agent",
    "create_coordinator_agent",
]

