from pathlib import Path

from charlie.agents.base import BaseAgentAdapter
from charlie.agents.registry import get_agent_spec
from charlie.schema import Command, CommandScripts


class SampleAdapter(BaseAgentAdapter):
    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        return f"Command: {namespace}.{command.name}"


def create_command(name="name", description="description", prompt="prompt", scripts=None) -> Command:
    return Command(name=name, description=description, prompt=prompt, scripts=scripts)


def test_adapter_initialization_sets_spec_and_root_directory() -> None:
    spec = get_agent_spec("claude")

    adapter = SampleAdapter(spec, root_dir="/test/root")

    assert adapter.spec == spec
    assert adapter.root_dir == "/test/root"


def test_transform_placeholders_replaces_user_input_with_agent_specific_placeholder() -> None:
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)
    command = create_command(prompt="Input: {{user_input}}")

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    assert result == "Input: $ARGUMENTS"


def test_transform_placeholders_replaces_script_placeholder_with_script_path() -> None:
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = create_command(
        prompt="Run: {{script}}",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    assert result == "Run: test.sh"


def test_transform_placeholders_replaces_user_input_with_toml_format_placeholder() -> None:
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


def test_get_script_path_returns_bash_script_when_requested() -> None:
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


def test_get_script_path_returns_powershell_script_when_requested() -> None:
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


def test_get_agent_script_path_returns_agent_script_when_defined() -> None:
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


def test_get_agent_script_path_returns_empty_string_when_none_defined() -> None:
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


def test_generate_commands_creates_output_directory_structure(tmp_path) -> None:
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

    expected_dir = tmp_path / ".claude" / "commands"
    assert expected_dir.exists()
    assert expected_dir.is_dir()


def test_generate_commands_creates_command_files_with_namespace(tmp_path) -> None:
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

    for filepath in files:
        assert Path(filepath).exists()


def test_transform_path_placeholders_replaces_all_path_placeholders() -> None:
    spec = get_agent_spec("cursor")
    adapter = SampleAdapter(spec, root_dir="/project/root")

    placeholders = {
        "{{root}}": "/project/root",
        "{{commands_dir}}": ".cursor/commands",
        "{{rules_dir}}": ".",
        "{{agent_dir}}": ".cursor",
    }

    for placeholder, value in placeholders.items():
        assert value == adapter.transform_path_placeholders(placeholder), f"Failed: {placeholder}"


def test_transform_path_placeholders_works_for_cursor_agent() -> None:
    spec = get_agent_spec("cursor")
    adapter = SampleAdapter(spec)

    text = "Use {{commands_dir}} for commands"
    result = adapter.transform_path_placeholders(text)

    assert ".cursor/commands" in result


def test_transform_placeholders_resolves_both_user_input_and_path_placeholders() -> None:
    spec = get_agent_spec("claude")
    adapter = SampleAdapter(spec)

    command = Command(
        name="test",
        description="Test",
        prompt="User wants: {{user_input}}\nCheck {{commands_dir}} for commands",
        scripts=CommandScripts(sh="test.sh"),
    )

    result = adapter.transform_placeholders(command.prompt, command, "sh")

    assert ".claude/commands" in result
    assert "$ARGUMENTS" in result
