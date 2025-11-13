import pytest

from charlie.agent_registry import AgentRegistry
from charlie.enums import FileFormat


def test_get_claude_agent() -> None:
    registry = AgentRegistry()
    agent = registry.get("claude")

    assert agent.name == "Claude Code"
    assert agent.shortname == "claude"
    assert agent.dir == ".claude"
    assert agent.default_format == FileFormat.MARKDOWN
    assert agent.commands_dir == ".claude/commands"
    assert agent.commands_extension == "md"
    assert agent.commands_shorthand_injection == "$ARGUMENTS"
    assert agent.rules_file == "CLAUDE.md"
    assert agent.rules_dir == ".claude/rules"
    assert agent.rules_extension == "md"
    assert agent.mcp_file == ".claude/mcp.json"


def test_get_cursor_agent() -> None:
    registry = AgentRegistry()
    agent = registry.get("cursor")

    assert agent.name == "Cursor"
    assert agent.shortname == "cursor"
    assert agent.dir == ".cursor"
    assert agent.default_format == FileFormat.MARKDOWN
    assert agent.commands_dir == ".cursor/commands"
    assert agent.commands_extension == "md"
    assert agent.commands_shorthand_injection == "$ARGUMENTS"
    assert agent.rules_file == ".cursor/rules"
    assert agent.rules_dir == ".cursor/rules"
    assert agent.rules_extension == "mdc"
    assert agent.mcp_file == ".cursor/mcp.json"


def test_get_copilot_agent() -> None:
    registry = AgentRegistry()
    agent = registry.get("copilot")

    assert agent.name == "GitHub Copilot"
    assert agent.shortname == "copilot"
    assert agent.dir == ".github"
    assert agent.default_format == FileFormat.MARKDOWN
    assert agent.commands_dir == ".github/prompts"
    assert agent.commands_extension == "prompt.md"
    assert agent.commands_shorthand_injection == "$ARGUMENTS"
    assert agent.rules_file == "copilot-instructions.md"
    assert agent.rules_dir == ".github/instructions"
    assert agent.rules_extension == "md"


def test_get_unknown_agent_raises_value_error() -> None:
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="Unknown agent: unknown"):
        registry.get("unknown")


def test_get_unknown_agent_error_message_includes_supported_agents() -> None:
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="Supported agents: claude, copilot, cursor"):
        registry.get("invalid")


def test_list_returns_all_agent_shortnames() -> None:
    registry = AgentRegistry()
    agents = registry.list()

    assert agents == ["claude", "copilot", "cursor"]


def test_list_returns_sorted_agent_shortnames() -> None:
    registry = AgentRegistry()
    agents = registry.list()

    assert agents == sorted(agents)


def test_get_is_case_sensitive() -> None:
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="Unknown agent: Claude"):
        registry.get("Claude")


def test_registry_contains_three_agents() -> None:
    registry = AgentRegistry()
    agents = registry.list()

    assert len(agents) == 3
