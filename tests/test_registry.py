"""Tests for agent registry."""

import pytest

from charlie.agents.registry import get_agent_spec, list_supported_agents


def test_get_agent_spec_valid() -> None:
    """Test getting spec for a valid agent."""
    spec = get_agent_spec("claude")

    assert spec.name == "Claude Code"
    assert spec.command_dir == ".claude/commands"
    assert spec.file_format == "markdown"


def test_get_agent_spec_invalid() -> None:
    """Test getting spec for invalid agent raises ValueError."""
    with pytest.raises(ValueError, match="Unknown agent"):
        get_agent_spec("nonexistent")


def test_list_supported_agents() -> None:
    """Test listing all supported agents."""
    agents = list_supported_agents()

    assert agents == sorted(agents)

def test_markdown_agents_have_correct_placeholder() -> None:
    """Test that markdown-format agents use $ARGUMENTS placeholder."""
    agent_specs = [get_agent_spec(name) for name in list_supported_agents()]
    markdown_agent_specs = [spec for spec in agent_specs if spec.file_format == "markdown"]

    for agent_spec in markdown_agent_specs:
        assert agent_spec.arg_placeholder == "$ARGUMENTS", f"Failed: {agent_spec.name}"


def test_toml_agents_have_correct_placeholder() -> None:
    """Test that TOML-format agents use {{args}} placeholder."""
    agent_specs = [get_agent_spec(name) for name in list_supported_agents()]
    toml_agents = [spec for spec in agent_specs if spec.file_format == "toml"]

    for agent_spec in toml_agents:
        assert agent_spec.arg_placeholder == "{{args}}"
