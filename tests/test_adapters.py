"""Tests for concrete agent adapters."""

import pytest
from pathlib import Path

from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.agents.registry import get_agent_spec
from charlie.schema import Command, CommandScripts


def test_claude_adapter_generates_markdown():
    """Test Claude adapter generates Markdown format."""
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}\nRun: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    # Check frontmatter
    assert "---" in result
    assert "description: Test command" in result

    # Check placeholders are transformed
    assert "$ARGUMENTS" in result
    assert "test.sh" in result
    assert "{{user_input}}" not in result
    assert "{{script}}" not in result


def test_copilot_adapter_generates_markdown():
    """Test Copilot adapter generates Markdown format."""
    spec = get_agent_spec("copilot")
    adapter = CopilotAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    assert "---" in result
    assert "description: Test command" in result
    assert "$ARGUMENTS" in result


def test_cursor_adapter_generates_markdown():
    """Test Cursor adapter generates Markdown format."""
    spec = get_agent_spec("cursor")
    adapter = CursorAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    assert "---" in result
    assert "description: Test command" in result
    assert "$ARGUMENTS" in result


def test_gemini_adapter_generates_toml():
    """Test Gemini adapter generates TOML format."""
    spec = get_agent_spec("gemini")
    adapter = GeminiAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}\nRun: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    # Check TOML format
    assert 'description = "Test command"' in result
    assert 'prompt = """' in result

    # Check placeholders are transformed to TOML format
    assert "{{args}}" in result
    assert "test.sh" in result
    assert "{{user_input}}" not in result
    assert "{{script}}" not in result


def test_qwen_adapter_generates_toml():
    """Test Qwen adapter generates TOML format."""
    spec = get_agent_spec("qwen")
    adapter = QwenAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    assert 'description = "Test command"' in result
    assert 'prompt = """' in result
    assert "{{args}}" in result


def test_adapters_use_powershell_scripts():
    """Test that adapters use PowerShell scripts when specified."""
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Run: {{script}}",
        scripts=CommandScripts(ps="test.ps1"),
    )

    result = adapter.generate_command(command, "myapp", "ps")
    assert "test.ps1" in result


def test_adapters_handle_agent_scripts():
    """Test that adapters handle agent_scripts placeholder."""
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="Run: {{script}}\nAgent script: {{agent_script}}",
        scripts=CommandScripts(sh="test.sh"),
        agent_scripts=CommandScripts(sh="agent.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")
    assert "test.sh" in result
    assert "agent.sh" in result


def test_adapters_pass_through_agent_fields():
    """Test that adapters include pass-through agent-specific fields."""
    # Test Claude (markdown) with allowed-tools
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    command = Command(
        name="commit",
        description="Git commit",
        prompt="Create commit",
        scripts=CommandScripts(sh="commit.sh"),
        allowed_tools=["Bash(git add:*)", "Bash(git commit:*)"],  # Claude-specific
        tags=["git", "vcs"],
        category="source-control",
    )

    result = adapter.generate_command(command, "myapp", "sh")
    
    # Check frontmatter includes pass-through fields
    assert "allowed_tools:" in result or "allowed-tools:" in result
    assert "Bash(git add:*)" in result
    assert "tags:" in result
    assert "- git" in result
    assert "category:" in result
    assert "source-control" in result

    # Test Gemini (TOML) with custom fields
    spec = get_agent_spec("gemini")
    adapter = GeminiAdapter(spec)
    
    command_toml = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="test.sh"),
        custom_field="custom_value",
    )
    
    result_toml = adapter.generate_command(command_toml, "myapp", "sh")
    assert 'custom_field = "custom_value"' in result_toml


def test_claude_adapter_generates_files(tmp_path):
    """Test Claude adapter generates command files."""
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    commands = [
        Command(
            name="init",
            description="Initialize",
            prompt="Init",
            scripts=CommandScripts(sh="init.sh"),
        )
    ]

    files = adapter.generate_commands(commands, "myapp", str(tmp_path))

    assert len(files) == 1
    assert ".claude/commands/myapp.init.md" in files[0]

    # Check file exists and has content
    filepath = Path(files[0])
    assert filepath.exists()
    content = filepath.read_text()
    assert "description: Initialize" in content


def test_gemini_adapter_generates_toml_files(tmp_path):
    """Test Gemini adapter generates TOML files."""
    spec = get_agent_spec("gemini")
    adapter = GeminiAdapter(spec)

    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            scripts=CommandScripts(sh="test.sh"),
        )
    ]

    files = adapter.generate_commands(commands, "myapp", str(tmp_path))

    assert len(files) == 1
    assert ".gemini/commands/myapp.test.toml" in files[0]

    # Check file has TOML content
    filepath = Path(files[0])
    content = filepath.read_text()
    assert 'description = "Test"' in content
    assert 'prompt = """' in content

