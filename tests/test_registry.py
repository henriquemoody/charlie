"""Tests for agent registry."""

import pytest

from charlie.agents.registry import (
    get_agent_spec,
    list_supported_agents,
    get_agent_info,
    AGENT_SPECS,
)


def test_get_agent_spec_valid():
    """Test getting spec for a valid agent."""
    spec = get_agent_spec("claude")
    assert spec["name"] == "Claude Code"
    assert spec["command_dir"] == ".claude/commands"
    assert spec["file_format"] == "markdown"


def test_get_agent_spec_invalid():
    """Test getting spec for invalid agent raises ValueError."""
    with pytest.raises(ValueError, match="Unknown agent"):
        get_agent_spec("nonexistent")


def test_list_supported_agents():
    """Test listing all supported agents."""
    agents = list_supported_agents()
    assert isinstance(agents, list)
    assert "claude" in agents
    assert "copilot" in agents
    assert "gemini" in agents
    assert len(agents) == len(AGENT_SPECS)
    # Should be sorted
    assert agents == sorted(agents)


def test_get_agent_info_valid():
    """Test getting agent info for valid agent."""
    info = get_agent_info("cursor")
    assert info is not None
    assert info["name"] == "Cursor"


def test_get_agent_info_invalid():
    """Test getting agent info for invalid agent returns None."""
    info = get_agent_info("nonexistent")
    assert info is None


def test_all_agents_have_required_fields():
    """Test that all agents have required fields."""
    required_fields = [
        "name",
        "command_dir",
        "rules_file",
        "file_format",
        "file_extension",
        "arg_placeholder",
    ]

    for agent_name, spec in AGENT_SPECS.items():
        for field in required_fields:
            assert field in spec, f"Agent {agent_name} missing field {field}"


def test_markdown_agents_have_correct_placeholder():
    """Test that markdown-format agents use $ARGUMENTS placeholder."""
    markdown_agents = [
        name
        for name, spec in AGENT_SPECS.items()
        if spec["file_format"] == "markdown"
    ]

    for agent_name in markdown_agents:
        spec = AGENT_SPECS[agent_name]
        assert spec["arg_placeholder"] == "$ARGUMENTS"


def test_toml_agents_have_correct_placeholder():
    """Test that TOML-format agents use {{args}} placeholder."""
    toml_agents = [
        name for name, spec in AGENT_SPECS.items() if spec["file_format"] == "toml"
    ]

    for agent_name in toml_agents:
        spec = AGENT_SPECS[agent_name]
        assert spec["arg_placeholder"] == "{{args}}"

