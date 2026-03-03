from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.assets_manager import AssetsManager
from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.configurators.copilot_configurator import CopilotConfigurator
from charlie.configurators.cursor_configurator import CursorConfigurator
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Project, Subagent


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(name="test-project", namespace=None, dir=str(tmp_path))


@pytest.fixture
def project_with_namespace(tmp_path: Path) -> Project:
    return Project(name="test-project", namespace="myapp", dir=str(tmp_path))


@pytest.fixture
def tracker() -> Mock:
    return Mock()


@pytest.fixture
def markdown_generator() -> MarkdownGenerator:
    return MarkdownGenerator()


@pytest.fixture
def mcp_server_generator(tracker: Mock) -> MCPServerGenerator:
    return MCPServerGenerator(tracker)


@pytest.fixture
def assets_manager(tracker: Mock) -> AssetsManager:
    return AssetsManager(tracker)


@pytest.fixture
def claude_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> ClaudeConfigurator:
    return ClaudeConfigurator(project, tracker, markdown_generator, mcp_server_generator, assets_manager, "claude")


@pytest.fixture
def cursor_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> CursorConfigurator:
    return CursorConfigurator(project, tracker, markdown_generator, mcp_server_generator, assets_manager, "cursor")


@pytest.fixture
def copilot_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> CopilotConfigurator:
    return CopilotConfigurator(project, tracker, markdown_generator, assets_manager, "copilot")


# ─── Claude configurator subagents ───────────────────────────────────────────


def test_claude_should_not_create_directory_when_no_subagents(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    claude_configurator.subagents([])

    subagents_dir = Path(project.dir) / ".claude/agents"
    assert not subagents_dir.exists()


def test_claude_should_create_agents_directory_when_subagents_provided(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [Subagent(name="code-reviewer", description="Reviews code", prompt="Review the code")]

    claude_configurator.subagents(subagents)

    subagents_dir = Path(project.dir) / ".claude/agents"
    assert subagents_dir.exists()
    assert subagents_dir.is_dir()


def test_claude_should_create_markdown_file_for_each_subagent(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(name="code-reviewer", description="Reviews code", prompt="Review the code"),
        Subagent(name="debugger", description="Debugs issues", prompt="Debug the issue"),
    ]

    claude_configurator.subagents(subagents)

    assert (Path(project.dir) / ".claude/agents/code-reviewer.md").exists()
    assert (Path(project.dir) / ".claude/agents/debugger.md").exists()


def test_claude_should_write_prompt_to_file_body(claude_configurator: ClaudeConfigurator, project: Project) -> None:
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="You are a senior code reviewer.")]

    claude_configurator.subagents(subagents)

    content = (Path(project.dir) / ".claude/agents/reviewer.md").read_text()
    assert "You are a senior code reviewer." in content


def test_claude_should_include_name_and_description_in_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [Subagent(name="code-reviewer", description="Expert code reviewer", prompt="Review code")]

    claude_configurator.subagents(subagents)

    content = (Path(project.dir) / ".claude/agents/code-reviewer.md").read_text()
    assert "name: code-reviewer" in content
    assert "description: Expert code reviewer" in content


def test_claude_should_include_allowed_metadata_in_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(
            name="reviewer",
            description="Reviews code",
            prompt="Review code",
            metadata={"tools": "Read, Grep, Glob", "model": "sonnet"},
        )
    ]

    claude_configurator.subagents(subagents)

    content = (Path(project.dir) / ".claude/agents/reviewer.md").read_text()
    assert "tools: Read, Grep, Glob" in content
    assert "model: sonnet" in content


def test_claude_should_filter_unknown_metadata_fields(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(
            name="reviewer",
            description="Reviews code",
            prompt="Review code",
            metadata={"unknown_field": "should_not_appear"},
        )
    ]

    claude_configurator.subagents(subagents)

    content = (Path(project.dir) / ".claude/agents/reviewer.md").read_text()
    assert "unknown_field" not in content


def test_claude_should_support_all_allowed_metadata_fields(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(
            name="reviewer",
            description="Reviews code",
            prompt="Review code",
            metadata={
                "tools": "Read, Grep",
                "disallowedTools": "Write",
                "model": "sonnet",
                "permissionMode": "acceptEdits",
                "maxTurns": 10,
                "memory": "project",
                "background": False,
                "isolation": "worktree",
            },
        )
    ]

    claude_configurator.subagents(subagents)

    content = (Path(project.dir) / ".claude/agents/reviewer.md").read_text()
    assert "tools: Read, Grep" in content
    assert "disallowedTools: Write" in content
    assert "permissionMode: acceptEdits" in content
    assert "maxTurns: 10" in content
    assert "memory: project" in content
    assert "isolation: worktree" in content


def test_claude_should_apply_namespace_prefix_to_filename(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = ClaudeConfigurator(
        project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager, "claude"
    )
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="Review code")]

    configurator.subagents(subagents)

    assert (Path(project_with_namespace.dir) / ".claude/agents/myapp-reviewer.md").exists()


def test_claude_should_track_each_subagent_file_created(
    claude_configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    subagents = [
        Subagent(name="reviewer", description="Reviews code", prompt="Review code"),
        Subagent(name="debugger", description="Debugs issues", prompt="Debug issues"),
    ]

    claude_configurator.subagents(subagents)

    assert tracker.track.call_count == 2
    tracked = [call[0][0] for call in tracker.track.call_args_list]
    assert any("reviewer.md" in str(f) for f in tracked)
    assert any("debugger.md" in str(f) for f in tracked)


def test_claude_should_not_track_when_no_subagents(claude_configurator: ClaudeConfigurator, tracker: Mock) -> None:
    claude_configurator.subagents([])

    tracker.track.assert_not_called()


def test_claude_placeholders_includes_subagents_dir(
    claude_configurator: ClaudeConfigurator,
) -> None:
    placeholders = claude_configurator.placeholders()

    assert "subagents_dir" in placeholders
    assert placeholders["subagents_dir"] == ".claude/agents"


# ─── Cursor configurator subagents ───────────────────────────────────────────


def test_cursor_should_not_create_directory_when_no_subagents(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    cursor_configurator.subagents([])

    subagents_dir = Path(project.dir) / ".cursor/agents"
    assert not subagents_dir.exists()


def test_cursor_should_create_agents_directory_when_subagents_provided(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    subagents = [Subagent(name="code-reviewer", description="Reviews code", prompt="Review the code")]

    cursor_configurator.subagents(subagents)

    subagents_dir = Path(project.dir) / ".cursor/agents"
    assert subagents_dir.exists()
    assert subagents_dir.is_dir()


def test_cursor_should_create_markdown_file_for_each_subagent(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(name="code-reviewer", description="Reviews code", prompt="Review the code"),
        Subagent(name="debugger", description="Debugs issues", prompt="Debug the issue"),
    ]

    cursor_configurator.subagents(subagents)

    assert (Path(project.dir) / ".cursor/agents/code-reviewer.md").exists()
    assert (Path(project.dir) / ".cursor/agents/debugger.md").exists()


def test_cursor_should_write_prompt_to_file_body(cursor_configurator: CursorConfigurator, project: Project) -> None:
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="You are a senior code reviewer.")]

    cursor_configurator.subagents(subagents)

    content = (Path(project.dir) / ".cursor/agents/reviewer.md").read_text()
    assert "You are a senior code reviewer." in content


def test_cursor_should_include_name_and_description_in_frontmatter(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    subagents = [Subagent(name="code-reviewer", description="Expert code reviewer", prompt="Review code")]

    cursor_configurator.subagents(subagents)

    content = (Path(project.dir) / ".cursor/agents/code-reviewer.md").read_text()
    assert "name: code-reviewer" in content
    assert "description: Expert code reviewer" in content


def test_cursor_should_include_cursor_specific_metadata(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(
            name="reviewer",
            description="Reviews code",
            prompt="Review code",
            metadata={"model": "inherit", "readonly": True},
        )
    ]

    cursor_configurator.subagents(subagents)

    content = (Path(project.dir) / ".cursor/agents/reviewer.md").read_text()
    assert "model: inherit" in content
    assert "readonly: true" in content


def test_cursor_should_filter_non_cursor_metadata(cursor_configurator: CursorConfigurator, project: Project) -> None:
    subagents = [
        Subagent(
            name="reviewer",
            description="Reviews code",
            prompt="Review code",
            metadata={"tools": "Read, Grep", "permissionMode": "acceptEdits"},
        )
    ]

    cursor_configurator.subagents(subagents)

    content = (Path(project.dir) / ".cursor/agents/reviewer.md").read_text()
    assert "tools" not in content
    assert "permissionMode" not in content


def test_cursor_should_apply_namespace_prefix_to_filename(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CursorConfigurator(
        project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager, "cursor"
    )
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="Review code")]

    configurator.subagents(subagents)

    assert (Path(project_with_namespace.dir) / ".cursor/agents/myapp.reviewer.md").exists()


def test_cursor_should_prefix_name_in_frontmatter_with_namespace(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CursorConfigurator(
        project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager, "cursor"
    )
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="Review code")]

    configurator.subagents(subagents)

    content = (Path(project_with_namespace.dir) / ".cursor/agents/myapp.reviewer.md").read_text()
    assert "name: myapp.reviewer" in content


def test_cursor_should_track_each_subagent_file_created(
    cursor_configurator: CursorConfigurator, tracker: Mock, project: Project
) -> None:
    subagents = [
        Subagent(name="reviewer", description="Reviews code", prompt="Review code"),
        Subagent(name="debugger", description="Debugs issues", prompt="Debug issues"),
    ]

    cursor_configurator.subagents(subagents)

    assert tracker.track.call_count == 2


def test_cursor_placeholders_includes_subagents_dir(
    cursor_configurator: CursorConfigurator,
) -> None:
    placeholders = cursor_configurator.placeholders()

    assert "subagents_dir" in placeholders
    assert placeholders["subagents_dir"] == ".cursor/agents"


# ─── Copilot configurator subagents ──────────────────────────────────────────


def test_copilot_should_track_skip_message_when_subagents_provided(
    copilot_configurator: CopilotConfigurator, tracker: Mock
) -> None:
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="Review code")]

    copilot_configurator.subagents(subagents)

    tracker.track.assert_called_once()
    assert "does not support subagents" in tracker.track.call_args[0][0]


def test_copilot_should_not_track_when_no_subagents(copilot_configurator: CopilotConfigurator, tracker: Mock) -> None:
    copilot_configurator.subagents([])

    tracker.track.assert_not_called()


def test_copilot_should_not_create_any_files_for_subagents(
    copilot_configurator: CopilotConfigurator, project: Project
) -> None:
    subagents = [Subagent(name="reviewer", description="Reviews code", prompt="Review code")]

    copilot_configurator.subagents(subagents)

    assert not (Path(project.dir) / ".github/agents").exists()


# ─── Config reader: directory-based subagent discovery ───────────────────────


def test_should_discover_subagent_files_in_charlie_agents_directory(tmp_path: Path) -> None:
    from charlie.config_reader import discover_charlie_files

    agents_dir = tmp_path / ".charlie" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text("---\ndescription: Reviews code\n---\nReview code")
    (agents_dir / "debugger.md").write_text("---\ndescription: Debugs issues\n---\nDebug issues")

    result = discover_charlie_files(tmp_path)

    assert len(result["subagents"]) == 2
    assert any("reviewer.md" in str(f) for f in result["subagents"])
    assert any("debugger.md" in str(f) for f in result["subagents"])


def test_should_return_empty_subagents_when_no_agents_directory(tmp_path: Path) -> None:
    from charlie.config_reader import discover_charlie_files

    (tmp_path / ".charlie").mkdir()

    result = discover_charlie_files(tmp_path)

    assert result["subagents"] == []


def test_should_parse_subagent_from_markdown_file(tmp_path: Path) -> None:
    from charlie.config_reader import parse_single_file
    from charlie.schema import Subagent

    agent_file = tmp_path / "reviewer.md"
    agent_file.write_text(
        "---\n"
        "description: Expert code reviewer\n"
        "tools: Read, Grep, Glob\n"
        "model: sonnet\n"
        "---\n"
        "You are a senior code reviewer.\n"
    )

    result = parse_single_file(agent_file, Subagent)

    assert result.name == "reviewer"
    assert result.description == "Expert code reviewer"
    assert result.prompt == "You are a senior code reviewer."
    assert result.metadata["tools"] == "Read, Grep, Glob"
    assert result.metadata["model"] == "sonnet"


def test_should_infer_subagent_name_from_filename_when_not_in_frontmatter(tmp_path: Path) -> None:
    from charlie.config_reader import parse_single_file
    from charlie.schema import Subagent

    agent_file = tmp_path / "code-reviewer.md"
    agent_file.write_text("---\ndescription: Reviews code\n---\nReview code")

    result = parse_single_file(agent_file, Subagent)

    assert result.name == "code-reviewer"


def test_should_load_subagents_from_directory_config(tmp_path: Path) -> None:
    from charlie.config_reader import load_directory_config

    agents_dir = tmp_path / ".charlie" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text("---\ndescription: Reviews code\n---\nYou are a code reviewer.")

    config = load_directory_config(tmp_path)

    assert len(config.subagents) == 1
    assert config.subagents[0].name == "reviewer"
    assert config.subagents[0].description == "Reviews code"
    assert config.subagents[0].prompt == "You are a code reviewer."


def test_should_load_subagents_from_yaml_config(tmp_path: Path) -> None:
    from charlie.config_reader import parse_config

    config_file = tmp_path / "charlie.yaml"
    config_file.write_text(
        "version: '1.0'\n"
        "project:\n"
        "  name: test\n"
        "subagents:\n"
        "  - name: reviewer\n"
        "    description: Reviews code\n"
        "    prompt: You are a code reviewer.\n"
    )

    config = parse_config(config_file)

    assert len(config.subagents) == 1
    assert config.subagents[0].name == "reviewer"
    assert config.subagents[0].description == "Reviews code"


def test_should_auto_slug_subagent_name_from_description_in_yaml(tmp_path: Path) -> None:
    from charlie.config_reader import parse_config

    config_file = tmp_path / "charlie.yaml"
    config_file.write_text(
        "version: '1.0'\n"
        "project:\n"
        "  name: test\n"
        "subagents:\n"
        "  - description: Code Reviewer Agent\n"
        "    prompt: You are a code reviewer.\n"
    )

    config = parse_config(config_file)

    assert config.subagents[0].name == "code-reviewer-agent"


# ─── Config merger: subagent merging ─────────────────────────────────────────


def test_should_merge_subagents_from_base_and_overlay(tmp_path: Path) -> None:
    from charlie.config_merger import merge_configs
    from charlie.schema import CharlieConfig

    project = Project(name="test", namespace=None, dir=str(tmp_path))
    base = CharlieConfig(
        project=project,
        subagents=[Subagent(name="reviewer", description="Reviews code", prompt="Review code")],
    )
    overlay = CharlieConfig(
        project=project,
        subagents=[Subagent(name="debugger", description="Debugs issues", prompt="Debug issues")],
    )

    result = merge_configs(base, overlay)

    assert len(result.config.subagents) == 2
    names = {s.name for s in result.config.subagents}
    assert names == {"reviewer", "debugger"}


def test_should_warn_and_override_duplicate_subagent_names(tmp_path: Path) -> None:
    from charlie.config_merger import merge_configs
    from charlie.schema import CharlieConfig

    project = Project(name="test", namespace=None, dir=str(tmp_path))
    base = CharlieConfig(
        project=project,
        subagents=[Subagent(name="reviewer", description="Old reviewer", prompt="Old prompt")],
    )
    overlay = CharlieConfig(
        project=project,
        subagents=[Subagent(name="reviewer", description="New reviewer", prompt="New prompt")],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.subagents) == 1
    assert result.config.subagents[0].description == "New reviewer"
    assert any("reviewer" in w for w in result.warnings)


# ─── Schema validation ────────────────────────────────────────────────────────


def test_should_raise_error_for_duplicate_subagent_names() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Duplicate subagent names"):
        from charlie.schema import CharlieConfig

        CharlieConfig(
            project=Project(name="test", namespace=None, dir="."),
            subagents=[
                Subagent(name="reviewer", description="First", prompt="First"),
                Subagent(name="reviewer", description="Second", prompt="Second"),
            ],
        )
