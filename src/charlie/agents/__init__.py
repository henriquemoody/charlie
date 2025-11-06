"""Agent adapters for different AI assistants."""

from charlie.agents.base import BaseAgentAdapter
from charlie.agents.registry import get_agent_info, get_agent_spec, list_supported_agents

__all__ = ["BaseAgentAdapter", "get_agent_spec", "list_supported_agents", "get_agent_info"]
