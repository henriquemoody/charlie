import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.enums import FileFormat, RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Agent, Command, HttpMCPServer, Project, Rule, StdioMCPServer


@pytest.fixture
def agent(tmp_path: Path) -> Agent:
    return Agent(
        name="Claude Code",
        shortname="claude",
        dir=str(tmp_path / ".claude"),
        default_format=FileFormat.MARKDOWN,
        commands_dir=".claude/commands",
        commands_extension="md",
        commands_shorthand_injection="$ARGUMENTS",
        rules_dir=".claude/rules",
        rules_file=str(tmp_path / "CLAUDE.md"),
        rules_extension="md",
        mcp_file=".claude/mcp.json",
    )


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
def configurator(
    agent: Agent, project: Project, tracker: Mock, markdown_generator: MarkdownGenerator
) -> ClaudeConfigurator:
    return ClaudeConfigurator(agent, project, tracker, markdown_generator)


def test_should_create_commands_directory_when_it_does_not_exist(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    commands_dir = Path(project.dir) / ".claude/commands"
    assert commands_dir.exists()
    assert commands_dir.is_dir()


def test_should_create_markdown_file_when_processing_each_command(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix issue", prompt="Fix the issue"),
        Command(name="review-pr", description="Review PR", prompt="Review pull request"),
    ]

    configurator.commands(commands)

    fix_file = Path(project.dir) / ".claude/commands/fix-issue.md"
    review_file = Path(project.dir) / ".claude/commands/review-pr.md"

    assert fix_file.exists()
    assert review_file.exists()


def test_should_write_prompt_to_file_body_when_creating_command(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Fix issue #$ARGUMENTS following our coding standards")]

    configurator.commands(commands)

    file = Path(project.dir) / ".claude/commands/test.md"
    content = file.read_text()

    assert "Fix issue #$ARGUMENTS following our coding standards" in content


def test_should_include_description_in_frontmatter_when_creating_command(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Fix a numbered issue", prompt="Fix issue")]

    configurator.commands(commands)

    file = Path(project.dir) / ".claude/commands/test.md"
    content = file.read_text()

    assert "description: Fix a numbered issue" in content


def test_should_include_allowed_tools_in_frontmatter_when_specified(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            metadata={"allowed-tools": "Bash(git add:*), Bash(git status:*)"},
        )
    ]

    configurator.commands(commands)

    file = Path(project.dir) / ".claude/commands/test.md"
    content = file.read_text()

    assert "allowed-tools: Bash(git add:*), Bash(git status:*)" in content


def test_should_include_argument_hint_in_frontmatter_when_specified(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            metadata={"argument-hint": "[pr-number] [priority]"},
        )
    ]

    configurator.commands(commands)

    file = Path(project.dir) / ".claude/commands/test.md"
    content = file.read_text()

    assert "argument-hint: '[pr-number] [priority]'" in content


def test_should_apply_namespace_prefix_to_filename_when_namespace_is_present(
    agent: Agent, project_with_namespace: Project, tracker: Mock, markdown_generator: MarkdownGenerator
) -> None:
    configurator = ClaudeConfigurator(agent, project_with_namespace, tracker, markdown_generator)
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".claude/commands/myapp-test.md"
    assert file.exists()


def test_should_track_each_file_when_creating_commands(
    configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix", prompt="Fix"),
        Command(name="review-pr", description="Review", prompt="Review"),
    ]

    configurator.commands(commands)

    assert tracker.track.call_count == 2
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("fix-issue.md" in str(f) for f in tracked_files)
    assert any("review-pr.md" in str(f) for f in tracked_files)


def test_should_filter_custom_metadata_when_not_in_allowed_list(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Prompt",
            metadata={"forbidden_field": "should_not_appear", "description": "Override desc"},
        )
    ]

    configurator.commands(commands)

    file = Path(project.dir) / ".claude/commands/test.md"
    content = file.read_text()

    assert "forbidden_field" not in content


def test_should_return_early_when_no_rules_provided(configurator: ClaudeConfigurator, tracker: Mock) -> None:
    configurator.rules([], RuleMode.MERGED)

    tracker.track.assert_not_called()


def test_should_create_claude_md_file_when_using_merged_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "CLAUDE.md"
    assert file.exists()


def test_should_include_project_name_as_header_when_using_merged_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "CLAUDE.md"
    content = file.read_text()

    assert "# test-project" in content


def test_should_include_all_rule_descriptions_as_headers_when_using_merged_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "CLAUDE.md"
    content = file.read_text()

    assert "## Code Style" in content
    assert "## Testing Guidelines" in content


def test_should_include_all_rule_prompts_when_using_merged_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black formatter"),
        Rule(name="testing", description="Testing", prompt="Write comprehensive tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "CLAUDE.md"
    content = file.read_text()

    assert "Use Black formatter" in content
    assert "Write comprehensive tests" in content


def test_should_not_have_trailing_newlines_when_using_merged_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "CLAUDE.md"
    content = file.read_text()

    assert not content.endswith("\n\n\n")
    assert content.endswith("\n") or not content.endswith("\n\n")


def test_should_track_created_file_when_using_merged_mode(
    configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    tracker.track.assert_called_once()
    assert "CLAUDE.md" in str(tracker.track.call_args[0][0])


def test_should_create_rules_directory_when_using_separate_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    rules_dir = Path(project.dir) / ".claude/rules"
    assert rules_dir.exists()
    assert rules_dir.is_dir()


def test_should_create_individual_rule_files_when_using_separate_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    style_file = Path(project.dir) / ".claude/rules/style.md"
    testing_file = Path(project.dir) / ".claude/rules/testing.md"

    assert style_file.exists()
    assert testing_file.exists()


def test_should_write_prompt_to_rule_file_when_using_separate_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black formatter for all code")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".claude/rules/style.md"
    content = file.read_text()

    assert "Use Black formatter for all code" in content


def test_should_create_claude_md_with_at_imports_when_using_separate_mode(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    claude_md = Path(project.dir) / "CLAUDE.md"
    content = claude_md.read_text()

    assert "# test-project" in content
    assert "## Code Style" in content
    assert "@.claude/rules/style.md" in content
    assert "## Testing Guidelines" in content
    assert "@.claude/rules/testing.md" in content


def test_should_apply_namespace_prefix_to_filename_when_using_separate_mode_with_namespace(
    agent: Agent, project_with_namespace: Project, tracker: Mock, markdown_generator: MarkdownGenerator
) -> None:
    configurator = ClaudeConfigurator(agent, project_with_namespace, tracker, markdown_generator)
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project_with_namespace.dir) / ".claude/rules/myapp-style.md"
    assert file.exists()


def test_should_track_rule_files_and_claude_md_when_using_separate_mode(
    configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    assert tracker.track.call_count == 3
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("style.md" in str(f) for f in tracked_files)
    assert any("testing.md" in str(f) for f in tracked_files)
    assert any("CLAUDE.md" in str(f) for f in tracked_files)


def test_should_return_early_when_no_mcp_servers_provided(configurator: ClaudeConfigurator, tracker: Mock) -> None:
    configurator.mcp_servers([])

    tracker.track.assert_not_called()


def test_should_create_json_file_when_processing_mcp_servers(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".claude/mcp.json"
    assert file.exists()


def test_should_write_valid_json_when_processing_mcp_servers(configurator: ClaudeConfigurator, project: Path) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx", args=["-y", "test-server"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".claude/mcp.json"
    with open(file) as f:
        data = json.load(f)

    assert "mcpServers" in data
    assert isinstance(data["mcpServers"], dict)


def test_should_include_server_configuration_without_name_field_when_processing_mcp_servers(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    servers = [
        StdioMCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"},
        )
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".claude/mcp.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcpServers"]["github"]
    assert server_config["command"] == "npx"
    assert server_config["args"] == ["-y", "@modelcontextprotocol/server-github"]
    assert server_config["env"] == {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"}
    assert "name" not in server_config


def test_should_handle_multiple_servers_when_processing_mcp_servers(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    servers = [
        StdioMCPServer(name="github", command="npx", args=["-y", "github-server"]),
        StdioMCPServer(name="filesystem", command="npx", args=["-y", "fs-server"]),
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".claude/mcp.json"
    with open(file) as f:
        data = json.load(f)

    assert "github" in data["mcpServers"]
    assert "filesystem" in data["mcpServers"]
    assert data["mcpServers"]["github"]["command"] == "npx"
    assert data["mcpServers"]["filesystem"]["command"] == "npx"


def test_should_handle_http_servers_when_processing_mcp_servers(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    servers = [
        HttpMCPServer(name="api-server", url="https://api.example.com", headers={"Authorization": "Bearer token"})
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".claude/mcp.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcpServers"]["api-server"]
    assert server_config["url"] == "https://api.example.com"
    assert server_config["headers"] == {"Authorization": "Bearer token"}
    assert server_config["transport"] == "http"


def test_should_track_created_file_when_processing_mcp_servers(
    configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx")]

    configurator.mcp_servers(servers)

    tracker.track.assert_called_once()
    assert str(Path(".claude") / "mcp.json") in str(tracker.track.call_args[0][0])


def test_should_create_mcp_directory_when_it_does_not_exist(configurator: ClaudeConfigurator, project: Project) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx")]

    configurator.mcp_servers(servers)

    mcp_dir = Path(project.dir) / ".claude"
    assert mcp_dir.exists()
    assert mcp_dir.is_dir()


def test_should_copy_file_to_destination_when_processing_assets(
    configurator: ClaudeConfigurator, project: Project, tmp_path: Path
) -> None:
    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("test content")

    assets = [str(source_file)]
    configurator.assets(assets)

    dest_file = tmp_path / ".claude/assets/test.txt"
    assert dest_file.exists()
    assert dest_file.read_text() == "test content"


def test_should_create_destination_directory_when_it_does_not_exist(
    configurator: ClaudeConfigurator, project: Project, tmp_path: Path
) -> None:
    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("content")

    assets = [str(source_file)]
    configurator.assets(assets)

    dest_dir = tmp_path / ".claude/assets"
    assert dest_dir.exists()
    assert dest_dir.is_dir()


def test_should_track_each_file_when_copying_assets(
    configurator: ClaudeConfigurator, tracker: Mock, tmp_path: Path, project: Project
) -> None:
    source1 = Path(project.dir) / ".charlie/assets/file1.txt"
    source2 = Path(project.dir) / ".charlie/assets/file2.txt"
    source1.parent.mkdir(parents=True, exist_ok=True)
    source1.write_text("content1")
    source2.write_text("content2")

    assets = [str(source1), str(source2)]
    configurator.assets(assets)

    assert tracker.track.call_count == 2


def test_should_handle_nested_directory_structure_when_copying_assets(
    configurator: ClaudeConfigurator, project: Project, tmp_path: Path
) -> None:
    source_file = Path(project.dir) / ".charlie/assets/subdir/nested.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("nested content")

    assets = [str(source_file)]
    configurator.assets(assets)

    dest_file = tmp_path / ".claude/assets/subdir/nested.txt"
    assert dest_file.exists()
    assert dest_file.read_text() == "nested content"
