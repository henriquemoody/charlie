import pytest

from charlie.agents.registry import get_agent_spec, list_supported_agents


def test_get_agent_spec_valid_agent_returns_spec_data() -> None:
    spec = get_agent_spec("claude")

    assert spec.name == "Claude Code"
    assert spec.command_dir == ".claude/commands"
    assert spec.file_format == "markdown"


def test_get_agent_spec_invalid_agent_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown agent"):
        get_agent_spec("nonexistent")


def test_list_supported_agents_returns_sorted_list() -> None:
    agents = list_supported_agents()

    assert agents == sorted(agents)


def test_markdown_agents_use_correct_arguments_placeholder() -> None:
    agent_specs = [get_agent_spec(name) for name in list_supported_agents()]
    markdown_agent_specs = [spec for spec in agent_specs if spec.file_format == "markdown"]

    for agent_spec in markdown_agent_specs:
        assert agent_spec.arg_placeholder == "$ARGUMENTS", f"Failed: {agent_spec.name}"


def test_toml_agents_use_correct_placeholder_format() -> None:
    agent_specs = [get_agent_spec(name) for name in list_supported_agents()]
    toml_agents = [spec for spec in agent_specs if spec.file_format == "toml"]

    for agent_spec in toml_agents:
        assert agent_spec.arg_placeholder == "{{args}}"
