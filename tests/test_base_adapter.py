"""Tests for base agent adapter."""

import pytest
from pathlib import Path

from charlie.agents.base import BaseAgentAdapter
from charlie.agents.registry import get_agent_spec
from charlie.schema import Command, CommandScripts


class SampleAdapter(BaseAgentAdapter):
    """Sample implementation of BaseAgentAdapter for testing."""

    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Simple test implementation."""
        return f"Command: {namespace}.{command.name}"


def test_adapter_initialization():
    """Test adapter initialization with agent spec."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)
    assert adapter.spec == spec


def test_transform_placeholders_user_input():
    """Test placeholder transformation for user input."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Input: {{user_input}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")
    assert result == "Input: $ARGUMENTS"


def test_transform_placeholders_script():
    """Test placeholder transformation for script."""
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Run: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")
    assert result == "Run: test.sh"


def test_transform_placeholders_toml_agent():
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


def test_get_script_path_sh():
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


def test_get_script_path_ps():
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


def test_get_agent_script_path():
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


def test_get_agent_script_path_none():
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


def test_generate_commands_creates_directory(tmp_path):
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

    files = adapter.generate_commands(commands, "myapp", str(tmp_path))

    # Check directory was created
    expected_dir = tmp_path / ".claude" / "commands"
    assert expected_dir.exists()
    assert expected_dir.is_dir()


def test_generate_commands_creates_files(tmp_path):
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

