import pytest

from charlie.enums import ScriptType
from charlie.schema import AgentSpec, Command, CommandScripts
from charlie.utils import PlaceholderTransformer


@pytest.fixture
def cursor_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="cursor",
        command_dir=".cursor/commands",
        rules_file=".cursorrules",
        file_format="markdown",
        file_extension=".mdc",
        arg_placeholder="{{args}}",
    )


@pytest.fixture
def claude_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="claude",
        command_dir=".claude/commands",
        rules_file=".claude/rules/.clinerules",
        file_format="markdown",
        file_extension=".md",
        arg_placeholder="$ARGUMENTS",
    )


@pytest.fixture
def sample_command() -> Command:
    return Command(
        name="test",
        description="Test command",
        prompt="Run test with {{user_input}}",
        scripts=CommandScripts(sh="scripts/test.sh", ps="scripts/test.ps1"),
    )


def test_transform_path_placeholders_replaces_root(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "The root is {{root}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "The root is /project/root"


def test_transform_path_placeholders_replaces_agent_dir(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "The agent dir is {{agent_dir}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "The agent dir is .cursor"


def test_transform_path_placeholders_replaces_commands_dir(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "The commands dir is {{commands_dir}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "The commands dir is .cursor/commands"


def test_transform_path_placeholders_replaces_rules_dir(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "The rules dir is {{rules_dir}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "The rules dir is ."


def test_transform_path_placeholders_replaces_rules_dir_with_subdirectory(claude_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(claude_agent_spec, root_dir="/project/root")

    text = "The rules dir is {{rules_dir}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "The rules dir is .claude/rules"


def test_transform_path_placeholders_replaces_all_placeholders(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Root: {{root}}, Agent: {{agent_dir}}, Commands: {{commands_dir}}, Rules: {{rules_dir}}"
    result = transformer.transform_path_placeholders(text)

    assert result == "Root: /project/root, Agent: .cursor, Commands: .cursor/commands, Rules: ."


def test_transform_content_placeholders_replaces_user_input(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Run with {{user_input}}"
    result = transformer.transform_content_placeholders(text, sample_command, ScriptType.SH.value)

    assert result == "Run with {{args}}"


def test_transform_content_placeholders_replaces_user_input_for_claude(
    claude_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(claude_agent_spec, root_dir="/project/root")

    text = "Run with {{user_input}}"
    result = transformer.transform_content_placeholders(text, sample_command, ScriptType.SH.value)

    assert result == "Run with $ARGUMENTS"


def test_transform_content_placeholders_replaces_script_sh(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Execute {{script}}"
    result = transformer.transform_content_placeholders(text, sample_command, ScriptType.SH.value)

    assert result == "Execute scripts/test.sh"


def test_transform_content_placeholders_replaces_script_ps(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Execute {{script}}"
    result = transformer.transform_content_placeholders(text, sample_command, ScriptType.PS.value)

    assert result == "Execute scripts/test.ps1"


def test_transform_content_placeholders_replaces_agent_script(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")
    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="scripts/test.sh"),
        agent_scripts=CommandScripts(sh="scripts/agent-test.sh"),
    )

    text = "Execute {{agent_script}}"
    result = transformer.transform_content_placeholders(text, command, ScriptType.SH.value)

    assert result == "Execute scripts/agent-test.sh"


def test_transform_content_placeholders_no_agent_script_leaves_placeholder(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Execute {{agent_script}}"
    result = transformer.transform_content_placeholders(text, sample_command, ScriptType.SH.value)

    # When there are no agent scripts, the placeholder should remain unchanged
    assert result == "Execute {{agent_script}}"


def test_transform_replaces_all_placeholders_with_command(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Root: {{root}}, Input: {{user_input}}, Script: {{script}}"
    result = transformer.transform(text, sample_command, ScriptType.SH.value)

    assert result == "Root: /project/root, Input: {{args}}, Script: scripts/test.sh"


def test_transform_replaces_only_path_placeholders_without_command(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    text = "Root: {{root}}, Input: {{user_input}}"
    result = transformer.transform(text)

    assert result == "Root: /project/root, Input: {{user_input}}"


def test_get_script_path_returns_empty_when_no_scripts(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")
    command = Command(name="test", description="Test", prompt="Test")

    result = transformer._get_script_path(command, ScriptType.SH.value)

    assert result == ""


def test_get_script_path_returns_sh_when_available(cursor_agent_spec: AgentSpec, sample_command: Command) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    result = transformer._get_script_path(sample_command, ScriptType.SH.value)

    assert result == "scripts/test.sh"


def test_get_script_path_returns_ps_when_available(cursor_agent_spec: AgentSpec, sample_command: Command) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    result = transformer._get_script_path(sample_command, ScriptType.PS.value)

    assert result == "scripts/test.ps1"


def test_get_script_path_fallback_to_sh_when_ps_requested_but_unavailable(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")
    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="scripts/test.sh"),
    )

    result = transformer._get_script_path(command, ScriptType.PS.value)

    assert result == "scripts/test.sh"


def test_get_agent_script_path_returns_empty_when_no_agent_scripts(
    cursor_agent_spec: AgentSpec, sample_command: Command
) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")

    result = transformer._get_agent_script_path(sample_command, ScriptType.SH.value)

    assert result == ""


def test_get_agent_script_path_returns_sh_when_available(cursor_agent_spec: AgentSpec) -> None:
    transformer = PlaceholderTransformer(cursor_agent_spec, root_dir="/project/root")
    command = Command(
        name="test",
        description="Test",
        prompt="Test",
        scripts=CommandScripts(sh="scripts/test.sh"),
        agent_scripts=CommandScripts(sh="scripts/agent-test.sh"),
    )

    result = transformer._get_agent_script_path(command, ScriptType.SH.value)

    assert result == "scripts/agent-test.sh"
