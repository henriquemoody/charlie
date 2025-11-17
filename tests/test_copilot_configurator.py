from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.agent_registry import AgentRegistry
from charlie.assets_manager import AssetsManager
from charlie.configurators.copilot_configurator import CopilotConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Agent, Command, HttpMCPServer, Project, Rule, StdioMCPServer


@pytest.fixture
def agent(tmp_path: Path) -> Agent:
    registry = AgentRegistry()
    agent = registry.get("copilot")
    # Override rules_file to use tmp_path for test isolation
    agent.rules_file = str(tmp_path / "copilot-instructions.md")
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
def assets_manager(tracker: Mock) -> AssetsManager:
    return AssetsManager(tracker)


@pytest.fixture
def configurator(
    agent: Agent,
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> CopilotConfigurator:
    return CopilotConfigurator(agent, project, tracker, markdown_generator, assets_manager)


def test_should_create_prompts_directory_when_it_does_not_exist(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    prompts_dir = Path(project.dir) / ".github/prompts"
    assert prompts_dir.exists()
    assert prompts_dir.is_dir()


def test_should_create_markdown_file_when_processing_each_command(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix issue", prompt="Fix the issue"),
        Command(name="review-pr", description="Review PR", prompt="Review pull request"),
    ]

    configurator.commands(commands)

    fix_file = Path(project.dir) / ".github/prompts/fix-issue.prompt.md"
    review_file = Path(project.dir) / ".github/prompts/review-pr.prompt.md"

    assert fix_file.exists()
    assert review_file.exists()


def test_should_write_prompt_to_file_body_when_creating_command(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Fix issue following our coding standards")]

    configurator.commands(commands)

    file = Path(project.dir) / ".github/prompts/test.prompt.md"
    content = file.read_text()

    assert "Fix issue following our coding standards" in content


def test_should_include_description_in_frontmatter_when_creating_command(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Fix a numbered issue", prompt="Fix issue")]

    configurator.commands(commands)

    file = Path(project.dir) / ".github/prompts/test.prompt.md"
    content = file.read_text()

    assert "description: Fix a numbered issue" in content


def test_should_apply_namespace_prefix_to_filename_when_namespace_is_present(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CopilotConfigurator(agent, project_with_namespace, tracker, markdown_generator, assets_manager)
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".github/prompts/myapp-test.prompt.md"
    assert file.exists()


def test_should_track_each_file_when_creating_commands(
    configurator: CopilotConfigurator, tracker: Mock, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix", prompt="Fix"),
        Command(name="review-pr", description="Review", prompt="Review"),
    ]

    configurator.commands(commands)

    # Should track 2 prompt files + 1 instructions file
    assert tracker.track.call_count == 3
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("fix-issue.prompt.md" in str(f) for f in tracked_files)
    assert any("review-pr.prompt.md" in str(f) for f in tracked_files)
    assert any("enable-slash-commands.md" in str(f) for f in tracked_files)


def test_should_create_instructions_file_when_processing_commands(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    instructions_file = Path(project.dir) / ".github/instructions/enable-slash-commands.md"
    assert instructions_file.exists()


def test_should_include_project_name_in_instructions_file_when_processing_commands(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    instructions_file = Path(project.dir) / ".github/instructions/enable-slash-commands.md"
    content = instructions_file.read_text()

    assert "You can use slash commands" in content


def test_should_list_available_commands_in_instructions_file_when_processing_commands(
    configurator: CopilotConfigurator, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix an issue", prompt="Fix"),
        Command(name="review-pr", description="Review a PR", prompt="Review"),
    ]

    configurator.commands(commands)

    instructions_file = Path(project.dir) / ".github/instructions/enable-slash-commands.md"
    content = instructions_file.read_text()

    assert "- `/fix-issue`: Fix an issue" in content
    assert "- `/review-pr`: Review a PR" in content


def test_should_filter_custom_metadata_when_not_in_allowed_list(
    configurator: CopilotConfigurator, project: Project
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

    file = Path(project.dir) / ".github/prompts/test.prompt.md"
    content = file.read_text()

    assert "forbidden_field" not in content


def test_should_return_early_when_no_rules_provided(configurator: CopilotConfigurator, tracker: Mock) -> None:
    configurator.rules([], RuleMode.MERGED)

    tracker.track.assert_not_called()


def test_should_create_instructions_file_when_using_merged_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "copilot-instructions.md"
    assert file.exists()


def test_should_include_project_name_as_header_when_using_merged_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "copilot-instructions.md"
    content = file.read_text()

    assert "# test-project" in content


def test_should_include_all_rule_descriptions_as_headers_when_using_merged_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "copilot-instructions.md"
    content = file.read_text()

    assert "## Code Style" in content
    assert "## Testing Guidelines" in content


def test_should_include_all_rule_prompts_when_using_merged_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black formatter"),
        Rule(name="testing", description="Testing", prompt="Write comprehensive tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "copilot-instructions.md"
    content = file.read_text()

    assert "Use Black formatter" in content
    assert "Write comprehensive tests" in content


def test_should_not_have_trailing_newlines_when_using_merged_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / "copilot-instructions.md"
    content = file.read_text()

    assert not content.endswith("\n\n\n")
    assert content.endswith("\n") or not content.endswith("\n\n")


def test_should_track_created_file_when_using_merged_mode(
    configurator: CopilotConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    tracker.track.assert_called_once()
    assert "copilot-instructions.md" in str(tracker.track.call_args[0][0])


def test_should_create_rules_directory_when_using_separate_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    rules_dir = Path(project.dir) / ".github/instructions"
    assert rules_dir.exists()
    assert rules_dir.is_dir()


def test_should_create_individual_rule_files_when_using_separate_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    style_file = Path(project.dir) / ".github/instructions/style-instructions.md"
    testing_file = Path(project.dir) / ".github/instructions/testing-instructions.md"

    assert style_file.exists()
    assert testing_file.exists()


def test_should_write_prompt_to_rule_file_when_using_separate_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black formatter for all code")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".github/instructions/style-instructions.md"
    content = file.read_text()

    assert "Use Black formatter for all code" in content


def test_should_create_instructions_file_with_at_imports_when_using_separate_mode(
    configurator: CopilotConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    instructions_file = Path(project.dir) / "copilot-instructions.md"
    content = instructions_file.read_text()

    assert "# test-project" in content
    assert "## Code Style" in content
    assert "See @.github/instructions/style-instructions.md" in content
    assert "## Testing Guidelines" in content
    assert "See @.github/instructions/testing-instructions.md" in content


def test_should_apply_namespace_prefix_to_filename_when_using_separate_mode_with_namespace(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CopilotConfigurator(agent, project_with_namespace, tracker, markdown_generator, assets_manager)
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project_with_namespace.dir) / ".github/instructions/myapp-style-instructions.md"
    assert file.exists()


def test_should_track_rule_files_and_instructions_file_when_using_separate_mode(
    configurator: CopilotConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    assert tracker.track.call_count == 3
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("style-instructions.md" in str(f) for f in tracked_files)
    assert any("testing-instructions.md" in str(f) for f in tracked_files)
    assert any("copilot-instructions.md" in str(f) for f in tracked_files)


def test_should_return_early_when_no_mcp_servers_provided(configurator: CopilotConfigurator, tracker: Mock) -> None:
    configurator.mcp_servers([])

    # Should not track anything when no servers provided
    tracker.track.assert_not_called()


def test_should_skip_and_track_message_when_processing_mcp_servers(
    configurator: CopilotConfigurator, tracker: Mock
) -> None:
    servers = [StdioMCPServer(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"])]

    configurator.mcp_servers(servers)

    # Should track skip message since GitHub Copilot doesn't support MCP servers
    tracker.track.assert_called_once_with("GitHub Copilot does not support MCP servers natively. Skipping...")


def test_should_not_create_files_when_processing_mcp_servers(
    configurator: CopilotConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx", args=["-y", "test-server"])]

    configurator.mcp_servers(servers)

    # Should not create any files since GitHub Copilot doesn't support MCP servers
    file = Path(project.dir) / ".github/copilot/mcp.json"
    assert not file.exists()


def test_should_track_skip_message_for_stdio_servers(configurator: CopilotConfigurator, tracker: Mock) -> None:
    servers = [
        StdioMCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"},
        )
    ]

    configurator.mcp_servers(servers)

    # Should track skip message for stdio servers
    tracker.track.assert_called_once_with("GitHub Copilot does not support MCP servers natively. Skipping...")


def test_should_track_skip_message_for_multiple_servers(configurator: CopilotConfigurator, tracker: Mock) -> None:
    servers = [
        StdioMCPServer(name="github", command="npx", args=["-y", "github-server"]),
        StdioMCPServer(name="filesystem", command="npx", args=["-y", "fs-server"]),
    ]

    configurator.mcp_servers(servers)

    # Should track skip message even with multiple servers
    tracker.track.assert_called_once_with("GitHub Copilot does not support MCP servers natively. Skipping...")


def test_should_track_skip_message_for_http_servers(configurator: CopilotConfigurator, tracker: Mock) -> None:
    servers = [
        HttpMCPServer(name="api-server", url="https://api.example.com", headers={"Authorization": "Bearer token"})
    ]

    configurator.mcp_servers(servers)

    # Should track skip message for http servers too
    tracker.track.assert_called_once_with("GitHub Copilot does not support MCP servers natively. Skipping...")


def test_should_track_skip_message_when_processing_mcp_servers(
    configurator: CopilotConfigurator, tracker: Mock
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx")]

    configurator.mcp_servers(servers)

    # Should track the skip message, not a file creation
    tracker.track.assert_called_once_with("GitHub Copilot does not support MCP servers natively. Skipping...")


def test_should_not_create_mcp_directory_when_it_does_not_exist(
    configurator: CopilotConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx")]

    configurator.mcp_servers(servers)

    # Should not create directory since GitHub Copilot doesn't support MCP servers
    mcp_dir = Path(project.dir) / ".github/copilot"
    assert not mcp_dir.exists()


def test_should_delegate_asset_copying_to_assets_manager(
    configurator: CopilotConfigurator, project: Project, tmp_path: Path
) -> None:
    """Test that assets() delegates to AssetsManager with correct paths."""
    # Mock the assets_manager
    configurator.assets_manager = Mock()

    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    assets = [str(source_file)]

    configurator.assets(assets)

    # Verify it calls assets_manager with correct arguments
    expected_source_base = Path(project.dir) / ".charlie" / "assets"
    expected_dest_base = Path(project.dir) / tmp_path / ".github" / "assets"

    configurator.assets_manager.copy_assets.assert_called_once_with(assets, expected_source_base, expected_dest_base)


def test_should_not_call_assets_manager_when_no_assets(
    configurator: CopilotConfigurator,
) -> None:
    """Test that assets() returns early when assets list is empty."""
    configurator.assets_manager = Mock()

    configurator.assets([])

    configurator.assets_manager.copy_assets.assert_not_called()


def test_should_not_create_file_when_copilot_does_not_support_ignore_files(
    configurator: CopilotConfigurator, project: Project
) -> None:
    patterns = ["*.log", ".env", "secrets/"]

    configurator.ignore_file(patterns)

    ignore_file = Path(project.dir) / ".github/.copilotignore"
    assert not ignore_file.exists()


def test_should_track_skip_message_when_ignore_file_called_for_copilot(
    configurator: CopilotConfigurator, tracker: Mock
) -> None:
    patterns = ["*.log"]

    configurator.ignore_file(patterns)

    tracker.track.assert_called_once()
    call_args = tracker.track.call_args[0][0]
    assert "GitHub Copilot does not support ignore files" in call_args
    assert "Skipping" in call_args
