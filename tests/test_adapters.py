from pathlib import Path

from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.agents.registry import get_agent_spec
from charlie.schema import Command, CommandScripts


def test_claude_adapter_generates_markdown_with_frontmatter_and_placeholders() -> None:
    spec = get_agent_spec("claude")
    adapter = ClaudeAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}\nRun: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    assert "---" in result
    assert "description: Test command" in result
    assert "$ARGUMENTS" in result
    assert "test.sh" in result
    assert "{{user_input}}" not in result
    assert "{{script}}" not in result


def test_copilot_adapter_generates_markdown_with_frontmatter_and_placeholders() -> None:
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


def test_cursor_adapter_generates_markdown_with_frontmatter_and_placeholders() -> None:
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


def test_gemini_adapter_generates_toml_with_placeholders_and_double_quotes() -> None:
    spec = get_agent_spec("gemini")
    adapter = GeminiAdapter(spec)

    command = Command(
        name="test",
        description="Test command",
        prompt="User input: {{user_input}}\nRun: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.generate_command(command, "myapp", "sh")

    assert 'description = "Test command"' in result
    assert 'prompt = """' in result
    assert "{{args}}" in result
    assert "test.sh" in result
    assert "{{user_input}}" not in result
    assert "{{script}}" not in result


def test_qwen_adapter_generates_toml_with_placeholders_and_double_quotes() -> None:
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


def test_adapters_use_powershell_scripts_when_specified_instead_of_bash() -> None:
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


def test_adapters_replace_agent_script_placeholder_with_agent_script_path() -> None:
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


def test_adapters_pass_through_agent_specific_fields_to_generated_content() -> None:
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

    assert "allowed_tools:" in result or "allowed-tools:" in result
    assert "Bash(git add:*)" in result
    assert "tags:" in result
    assert "- git" in result
    assert "category:" in result
    assert "source-control" in result

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


def test_claude_adapter_generates_markdown_files_in_correct_directory_structure(tmp_path) -> None:
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
    # Normalize path separators for cross-platform comparison
    normalized_path = files[0].replace("\\", "/")
    assert ".claude/commands/myapp.init.md" in normalized_path

    filepath = Path(files[0])
    assert filepath.exists()
    content = filepath.read_text()
    assert "description: Initialize" in content


def test_gemini_adapter_generates_toml_files_in_correct_directory_structure(tmp_path) -> None:
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
    # Normalize path separators for cross-platform comparison
    normalized_path = files[0].replace("\\", "/")
    assert ".gemini/commands/myapp.test.toml" in normalized_path

    filepath = Path(files[0])
    content = filepath.read_text()
    assert 'description = "Test"' in content
    assert 'prompt = """' in content
