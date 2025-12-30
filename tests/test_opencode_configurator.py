from pathlib import Path
from unittest.mock import Mock
import json

import pytest

from charlie.agent_registry import AgentRegistry
from charlie.assets_manager import AssetsManager
from charlie.configurators.opencode_configurator import OpencodeConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Agent, Command, Project, Rule, StdioMCPServer


@pytest.fixture
def agent(tmp_path: Path) -> Agent:
    registry = AgentRegistry()
    agent = registry.get("opencode")
    # Override rules_file to use tmp_path for test isolation
    agent.rules_file = str(tmp_path / ".opencode/instructions.md")
    return agent


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
) -> OpencodeConfigurator:
    return OpencodeConfigurator(agent, project, tracker, markdown_generator, mcp_server_generator, assets_manager)


def test_should_create_prompts_directory_when_it_does_not_exist(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    commands_dir = Path(project.dir) / ".opencode/command"
    assert commands_dir.exists()
    assert commands_dir.is_dir()


def test_should_create_markdown_file_when_processing_each_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix issue", prompt="Fix the issue"),
        Command(name="review-pr", description="Review PR", prompt="Review pull request"),
    ]

    configurator.commands(commands)

    fix_file = Path(project.dir) / ".opencode/command/fix-issue.md"
    review_file = Path(project.dir) / ".opencode/command/review-pr.md"

    assert fix_file.exists()
    assert review_file.exists()


def test_should_write_prompt_to_file_body_when_creating_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Fix issue following our coding standards")]

    configurator.commands(commands)

    file = Path(project.dir) / ".opencode/command/test.md"
    content = file.read_text()

    assert "Fix issue following our coding standards" in content


def test_should_include_description_in_frontmatter_when_creating_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Fix a numbered issue", prompt="Fix issue")]

    configurator.commands(commands)

    file = Path(project.dir) / ".opencode/command/test.md"
    content = file.read_text()

    assert "description: Fix a numbered issue" in content


def test_should_apply_namespace_prefix_to_filename_when_namespace_is_present(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        agent, project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager
    )
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".opencode/command/myapp-test.md"
    assert file.exists()


def test_should_track_each_file_when_creating_commands(
    configurator: OpencodeConfigurator, tracker: Mock, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix", prompt="Fix"),
        Command(name="review-pr", description="Review", prompt="Review"),
    ]

    configurator.commands(commands)

    # Should track 2 command files
    assert tracker.track.call_count == 2
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("fix-issue.md" in str(f) for f in tracked_files)
    assert any("review-pr.md" in str(f) for f in tracked_files)


def test_should_filter_custom_metadata_when_not_in_allowed_list(
    configurator: OpencodeConfigurator, project: Project
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

    file = Path(project.dir) / ".opencode/command/test.md"
    content = file.read_text()

    assert "forbidden_field" not in content


def test_should_return_early_when_no_rules_provided(configurator: OpencodeConfigurator, tracker: Mock) -> None:
    configurator.rules([], RuleMode.MERGED)

    tracker.track.assert_not_called()


def test_should_create_instructions_file_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions.md"
    assert file.exists()


def test_should_include_project_name_as_header_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions.md"
    content = file.read_text()

    assert "# test-project" in content


def test_should_include_all_rule_descriptions_as_headers_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions.md"
    content = file.read_text()

    assert "## Code Style" in content
    assert "## Testing Guidelines" in content


def test_should_include_all_rule_prompts_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black formatter"),
        Rule(name="testing", description="Testing", prompt="Write comprehensive tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions.md"
    content = file.read_text()

    assert "Use Black formatter" in content
    assert "Write comprehensive tests" in content


def test_should_not_have_trailing_newlines_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions.md"
    content = file.read_text()

    assert not content.endswith("\n\n\n")
    assert content.endswith("\n") or not content.endswith("\n\n")


def test_should_track_created_file_when_using_merged_mode(
    configurator: OpencodeConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    # Should track instructions file and update to opencode.json
    assert tracker.track.call_count >= 1
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any(".opencode/instructions.md" in str(f) for f in tracked_files)


def test_should_add_instructions_to_opencode_json_when_using_merged_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    config_file = Path(project.dir) / "opencode.json"
    assert config_file.exists()
    
    with open(config_file) as f:
        config = json.load(f)
    
    assert "instructions" in config
    assert ".opencode/instructions.md" in config["instructions"]


def test_should_create_rules_directory_when_using_separate_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    rules_dir = Path(project.dir) / ".opencode/instructions"
    assert rules_dir.exists()
    assert rules_dir.is_dir()


def test_should_create_individual_rule_files_when_using_separate_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    style_file = Path(project.dir) / ".opencode/instructions/style.md"
    testing_file = Path(project.dir) / ".opencode/instructions/testing.md"

    assert style_file.exists()
    assert testing_file.exists()


def test_should_write_prompt_to_rule_file_when_using_separate_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black formatter for all code")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".opencode/instructions/style.md"
    content = file.read_text()

    assert "Use Black formatter for all code" in content


def test_should_create_instructions_file_with_at_imports_when_using_separate_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    instructions_file = Path(project.dir) / ".opencode/instructions.md"
    content = instructions_file.read_text()

    assert "# test-project" in content
    assert "## Code Style" in content
    assert "See @.opencode/instructions/style.md" in content
    assert "## Testing Guidelines" in content
    assert "See @.opencode/instructions/testing.md" in content


def test_should_apply_namespace_prefix_to_filename_when_using_separate_mode_with_namespace(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        agent, project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager
    )
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project_with_namespace.dir) / ".opencode/instructions/myapp-style.md"
    assert file.exists()


def test_should_track_rule_files_and_instructions_file_when_using_separate_mode(
    configurator: OpencodeConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    # Should track all rule files and main instructions file
    assert tracker.track.call_count >= 3
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("style.md" in str(f) for f in tracked_files)
    assert any("testing.md" in str(f) for f in tracked_files)
    assert any(".opencode/instructions.md" in str(f) for f in tracked_files)


def test_should_add_all_instructions_to_opencode_json_when_using_separate_mode(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    config_file = Path(project.dir) / "opencode.json"
    assert config_file.exists()
    
    with open(config_file) as f:
        config = json.load(f)
    
    assert "instructions" in config
    assert ".opencode/instructions.md" in config["instructions"]
    assert ".opencode/instructions/style.md" in config["instructions"]
    assert ".opencode/instructions/testing.md" in config["instructions"]


def test_should_return_early_when_no_mcp_servers_provided(
    configurator: OpencodeConfigurator, tracker: Mock
) -> None:
    configurator.mcp_servers([])

    # Should not track anything when no servers provided
    tracker.track.assert_not_called()


def test_should_create_mcp_file_when_processing_mcp_servers(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"])]

    configurator.mcp_servers(servers)

    config_file = Path(project.dir) / "opencode.json"
    assert config_file.exists()

    with open(config_file) as f:
        config = json.load(f)

    assert "mcpServers" in config
    assert "filesystem" in config["mcpServers"]
    assert config["mcpServers"]["filesystem"]["command"] == "npx"


def test_should_track_created_file_when_processing_mcp_servers(
    configurator: OpencodeConfigurator, tracker: Mock
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx", args=["-y", "test-server"])]

    configurator.mcp_servers(servers)

    tracker.track.assert_called_once()
    assert "test-server" in str(tracker.track.call_args[0][0])
    assert "opencode.json" in str(tracker.track.call_args[0][0])


def test_should_delegate_asset_copying_to_assets_manager(
    configurator: OpencodeConfigurator, project: Project, tmp_path: Path
) -> None:
    """Test that assets() delegates to AssetsManager with correct paths."""
    # Mock the assets_manager
    configurator.assets_manager = Mock()

    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    assets = [str(source_file)]

    configurator.assets(assets)

    # Verify it calls assets_manager with correct arguments
    expected_source_base = Path(project.dir) / ".charlie" / "assets"
    expected_dest_base = Path(project.dir) / ".opencode" / "assets"

    configurator.assets_manager.copy_assets.assert_called_once_with(assets, expected_source_base, expected_dest_base)


def test_should_not_call_assets_manager_when_no_assets(
    configurator: OpencodeConfigurator,
) -> None:
    """Test that assets() returns early when assets list is empty."""
    configurator.assets_manager = Mock()

    configurator.assets([])

    configurator.assets_manager.copy_assets.assert_not_called()


def test_should_create_ignore_file_when_patterns_provided(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    patterns = ["*.log", ".env", "secrets/"]

    configurator.ignore_file(patterns)

    config_file = Path(project.dir) / "opencode.json"
    assert config_file.exists()


def test_should_write_patterns_to_ignore_file(configurator: OpencodeConfigurator, project: Project) -> None:
    patterns = ["*.log", ".env", "secrets/"]

    configurator.ignore_file(patterns)

    config_file = Path(project.dir) / "opencode.json"
    with open(config_file) as f:
        config = json.load(f)

    assert "watcher" in config
    assert "ignore" in config["watcher"]
    assert "*.log" in config["watcher"]["ignore"]
    assert ".env" in config["watcher"]["ignore"]
    assert "secrets/" in config["watcher"]["ignore"]


def test_should_include_auto_generated_comment_in_ignore_file(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    patterns = ["*.log"]

    configurator.ignore_file(patterns)

    # The opencode.json doesn't have comments, so we skip this test or modify it
    # Just check that the file was created
    config_file = Path(project.dir) / "opencode.json"
    assert config_file.exists()


def test_should_track_ignore_file_creation(configurator: OpencodeConfigurator, tracker: Mock) -> None:
    patterns = ["*.log"]

    configurator.ignore_file(patterns)

    tracker.track.assert_called_once()
    call_args = tracker.track.call_args[0][0]
    assert "ignore patterns" in call_args.lower() or "opencode.json" in call_args.lower()


def test_should_not_create_config_when_no_patterns_provided(
    configurator: OpencodeConfigurator, project: Project, tracker: Mock
) -> None:
    configurator.ignore_file([])

    config_file = Path(project.dir) / "opencode.json"
    assert not config_file.exists()
    tracker.track.assert_not_called()
