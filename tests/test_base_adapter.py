"""Tests for base agent adapter."""

from pathlib import Path

from charlie.agents.base import BaseAgentAdapter
from charlie.agents.registry import get_agent_spec
from charlie.schema import Command, CommandScripts


class SampleAdapter(BaseAgentAdapter):
    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        return f"Command: {namespace}.{command.name}"

def create_command(
    name="name",
    description="description",
    prompt="prompt",
    scripts=None
) -> Command:
    return Command(name=name, description=description, prompt=prompt, scripts=scripts)

def test_adapter_initialization() -> None:
    spec = get_agent_spec("claude")

    adapter = SampleAdapter(spec, root_dir="/test/root")

    assert adapter.spec == spec
    assert adapter.root_dir == "/test/root"


def test_transform_placeholders_user_input() -> None:
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)
    command = create_command(prompt="Input: {{user_input}}")

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    assert result == "Input: $ARGUMENTS"


def test_transform_placeholders_script() -> None:
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = create_command(
        prompt="Run: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    assert result == "Run: test.sh"


def test_transform_placeholders_toml_agent() -> None:
    """Test placeholder transformation for TOML agent (Gemini)."""
    spec = get_agent_spec("gemini")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Input: {{user_input}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")
    assert result == "Input: {{args}}"


def test_get_script_path_sh() -> None:
    """Test getting script path for bash."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="test.sh", ps="test.ps1"),
    )

    script_path = adapter._get_script_path(command, "sh")
    assert script_path == "test.sh"


def test_get_script_path_ps() -> None:
    """Test getting script path for PowerShell."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="test.sh", ps="test.ps1"),
    )

    script_path = adapter._get_script_path(command, "ps")
    assert script_path == "test.ps1"


def test_get_agent_script_path() -> None:
    """Test getting agent script path."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="test.sh"),
        agent_scripts=CommandScripts(sh="agent.sh"),
    )

    agent_script = adapter._get_agent_script_path(command, "sh")
    assert agent_script == "agent.sh"


def test_get_agent_script_path_none() -> None:
    """Test getting agent script path when none defined."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="test.sh"),
    )

    agent_script = adapter._get_agent_script_path(command, "sh")
    assert agent_script == ""


def test_generate_commands_creates_directory(tmp_path) -> None:
    """Test that generate_commands creates output directory."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            scripts=CommandScripts(sh="test.sh"),
        )
    ]

    adapter.generate_commands(commands, "myapp", str(tmp_path))

    # Check directory was created
    expected_dir = tmp_path / ".claude" / "commands"
    assert expected_dir.exists()
    assert expected_dir.is_dir()


def test_generate_commands_creates_files(tmp_path) -> None:
    """Test that generate_commands creates command files."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    commands = [
        Command(
            name="init",
            description="Initialize",
            prompt="Init prompt",
            scripts=CommandScripts(sh="init.sh"),
        ),
        Command(
            name="plan",
            description="Plan",
            prompt="Plan prompt",
            scripts=CommandScripts(sh="plan.sh"),
        ),
    ]

    files = adapter.generate_commands(commands, "myapp", str(tmp_path))

    assert len(files) == 2
    assert any("myapp.init.md" in f for f in files)
    assert any("myapp.plan.md" in f for f in files)

    # Check files exist
    for filepath in files:
        assert Path(filepath).exists()


def test_transform_path_placeholders() -> None:
    """Test path placeholder transformation."""
    spec = get_agent_spec("cursor")
    adapter = SampleAdapter(spec, root_dir="/project/root")

    placeholders = {
        "{{root}}": "/project/root",
        "{{commands_dir}}": ".cursor/commands",
        "{{rules_dir}}": ".",
        "{{agent_dir}}": ".cursor"
    }

    for placeholder, value in placeholders.items():
        assert value == adapter.transform_path_placeholders(placeholder), f"Failed: {placeholder}"


def test_transform_path_placeholders_cursor() -> None:
    """Test path placeholders for Cursor agent."""
    spec = get_agent_spec("cursor")
    adapter = SampleAdapter(spec)

    text = "Use {{commands_dir}} for commands"
    result = adapter.transform_path_placeholders(text)

    assert ".cursor/commands" in result


def test_transform_path_placeholders_in_transform_placeholders() -> None:
    """Test that path placeholders are resolved in transform_placeholders."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="User wants: {{user_input}}\nCheck {{commands_dir}} for commands",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    # Path placeholder should be resolved
    assert ".claude/commands" in result
    # User input placeholder should also be resolved
    assert "$ARGUMENTS" in result
