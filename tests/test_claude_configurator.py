import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.assets_manager import AssetsManager
from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.enums import FileFormat, RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
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
        ignore_file=".claude/settings.local.json",
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
def mcp_server_generator(tracker: Mock) -> MCPServerGenerator:
    return MCPServerGenerator(tracker)


@pytest.fixture
def assets_manager(tracker: Mock) -> AssetsManager:
    return AssetsManager(tracker)


@pytest.fixture
def configurator(
    agent: Agent,
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> ClaudeConfigurator:
    return ClaudeConfigurator(agent, project, tracker, markdown_generator, mcp_server_generator, assets_manager)


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
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = ClaudeConfigurator(
        agent,
        project_with_namespace,
        tracker,
        markdown_generator,
        mcp_server_generator,
        assets_manager,
    )
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
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = ClaudeConfigurator(
        agent,
        project_with_namespace,
        tracker,
        markdown_generator,
        mcp_server_generator,
        assets_manager,
    )
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
    assert server_config["type"] == "http"


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


def test_should_delegate_asset_copying_to_assets_manager(
    configurator: ClaudeConfigurator, project: Project, tmp_path: Path
) -> None:
    """Test that assets() delegates to AssetsManager with correct paths."""
    # Mock the assets_manager
    configurator.assets_manager = Mock()

    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    assets = [str(source_file)]

    configurator.assets(assets)

    # Verify it calls assets_manager with correct arguments
    expected_source_base = Path(project.dir) / ".charlie" / "assets"
    expected_dest_base = Path(tmp_path / ".claude") / "assets"

    configurator.assets_manager.copy_assets.assert_called_once_with(assets, expected_source_base, expected_dest_base)


def test_should_not_call_assets_manager_when_no_assets(
    configurator: ClaudeConfigurator,
) -> None:
    """Test that assets() returns early when assets list is empty."""
    configurator.assets_manager = Mock()

    configurator.assets([])

    configurator.assets_manager.copy_assets.assert_not_called()


def test_should_write_deny_rules_to_settings_when_ignore_patterns_provided(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    patterns = [".charlie", "*.log", ".env", "secrets/"]

    configurator.ignore_file(patterns)

    settings_file = Path(project.dir) / ".claude/settings.local.json"
    assert settings_file.exists()

    import json

    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)

    assert "permissions" in settings
    assert "deny" in settings["permissions"]
    deny_rules = settings["permissions"]["deny"]
    assert "Read(.charlie)" in deny_rules
    assert "Read(*.log)" in deny_rules
    assert "Read(.env)" in deny_rules
    assert "Read(secrets/)" in deny_rules


def test_should_preserve_existing_settings_when_updating_deny_rules(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    settings_file = Path(project.dir) / ".claude/settings.local.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    import json

    existing_settings = {"permissions": {"deny": ["Read(.env)"], "allow": ["Bash(git:*)"]}, "otherSetting": "value"}
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(existing_settings, f)

    patterns = [".charlie", "*.log", "secrets/"]
    configurator.ignore_file(patterns)

    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)

    assert settings["otherSetting"] == "value"
    assert settings["permissions"]["allow"] == ["Bash(git:*)"]

    deny_rules = settings["permissions"]["deny"]
    assert "Read(.env)" in deny_rules
    assert "Read(.charlie)" in deny_rules
    assert "Read(*.log)" in deny_rules
    assert "Read(secrets/)" in deny_rules


def test_should_not_duplicate_rules_when_pattern_already_exists(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    settings_file = Path(project.dir) / ".claude/settings.local.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    import json

    existing_settings = {"permissions": {"deny": ["Read(.charlie)", "Read(*.log)"]}}
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(existing_settings, f)

    patterns = [".charlie", "*.log", ".env"]
    configurator.ignore_file(patterns)

    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)

    deny_rules = settings["permissions"]["deny"]
    assert deny_rules.count("Read(.charlie)") == 1
    assert deny_rules.count("Read(*.log)") == 1
    assert "Read(.env)" in deny_rules


def test_should_create_valid_settings_when_existing_file_is_corrupted(
    configurator: ClaudeConfigurator, project: Project
) -> None:
    settings_file = Path(project.dir) / ".claude/settings.local.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    with open(settings_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")

    patterns = ["*.log"]
    configurator.ignore_file(patterns)

    import json

    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)

    assert "permissions" in settings
    assert "deny" in settings["permissions"]


def test_should_not_create_file_when_patterns_list_is_empty(
    configurator: ClaudeConfigurator, project: Project, tracker: Mock
) -> None:
    configurator.ignore_file([])

    settings_file = Path(project.dir) / ".claude/settings.local.json"
    assert not settings_file.exists()

    tracker.track.assert_called_once_with("No ignore patterns to add for Claude Code")


def test_should_not_create_file_when_agent_ignore_file_is_none(
    agent: Agent,
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    agent_without_ignore = Agent(
        name="Test Agent",
        shortname="test",
        dir=".test",
        default_format=agent.default_format,
        commands_dir=".test/commands",
        commands_extension="md",
        commands_shorthand_injection="$ARGS",
        rules_dir=".test/rules",
        rules_file="TEST.md",
        rules_extension="md",
        mcp_file=".test/mcp.json",
        ignore_file=None,
    )
    configurator = ClaudeConfigurator(
        agent_without_ignore, project, tracker, markdown_generator, mcp_server_generator, assets_manager
    )

    configurator.ignore_file(["*.log"])

    settings_file = Path(project.dir) / ".claude/settings.local.json"
    assert not settings_file.exists()


def test_should_track_configuration_and_update_when_writing_settings(
    configurator: ClaudeConfigurator, project: Project, tracker: Mock
) -> None:
    patterns = [".charlie", "*.log"]

    configurator.ignore_file(patterns)

    assert tracker.track.call_count == 2

    first_call_args = tracker.track.call_args_list[0][0][0]
    assert "Configuring Claude Code ignore patterns" in first_call_args

    second_call_args = tracker.track.call_args_list[1][0][0]
    assert "Updated ignore patterns" in second_call_args
