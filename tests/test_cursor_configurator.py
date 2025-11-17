import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.assets_manager import AssetsManager
from charlie.configurators.cursor_configurator import CursorConfigurator
from charlie.enums import FileFormat, RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Agent, Command, HttpMCPServer, Project, Rule, StdioMCPServer


@pytest.fixture
def agent(tmp_path: Path) -> Agent:
    return Agent(
        name="Cursor",
        shortname="cursor",
        dir=str(tmp_path / ".cursorrules"),
        default_format=FileFormat.MARKDOWN,
        commands_dir=".cursorrules/commands",
        commands_extension="md",
        commands_shorthand_injection="{{shorthand}}",
        rules_dir=".cursorrules/rules",
        rules_file=str(tmp_path / ".cursorrules/rules.md"),
        rules_extension="md",
        mcp_file=".cursorrules/mcp.json",
        ignore_file=".cursorignore",
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
) -> CursorConfigurator:
    return CursorConfigurator(agent, project, tracker, markdown_generator, mcp_server_generator, assets_manager)


def test_should_create_commands_directory_when_it_does_not_exist(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    commands_dir = Path(project.dir) / ".cursorrules/commands"
    assert commands_dir.exists()
    assert commands_dir.is_dir()


def test_should_create_markdown_file_when_processing_each_command(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [
        Command(name="init", description="Initialize", prompt="Initialize project"),
        Command(name="build", description="Build", prompt="Build project"),
    ]

    configurator.commands(commands)

    init_file = Path(project.dir) / ".cursorrules/commands/init.md"
    build_file = Path(project.dir) / ".cursorrules/commands/build.md"

    assert init_file.exists()
    assert build_file.exists()


def test_should_write_prompt_to_file_body_when_creating_command(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="This is the prompt content")]

    configurator.commands(commands)

    file = Path(project.dir) / ".cursorrules/commands/test.md"
    content = file.read_text()

    assert "This is the prompt content" in content


def test_should_include_description_in_frontmatter_when_creating_command(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test description", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project.dir) / ".cursorrules/commands/test.md"
    content = file.read_text()

    assert "description: Test description" in content


def test_should_include_name_in_frontmatter_when_creating_command(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project.dir) / ".cursorrules/commands/test.md"
    content = file.read_text()

    assert "name: test" in content


def test_should_apply_namespace_to_filename_when_namespace_is_present(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CursorConfigurator(
        agent,
        project_with_namespace,
        tracker,
        markdown_generator,
        mcp_server_generator,
        assets_manager,
    )
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".cursorrules/commands/myapp.test.md"
    assert file.exists()


def test_should_apply_namespace_to_name_in_frontmatter_when_namespace_is_present(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CursorConfigurator(
        agent,
        project_with_namespace,
        tracker,
        markdown_generator,
        mcp_server_generator,
        assets_manager,
    )
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".cursorrules/commands/myapp.test.md"
    content = file.read_text()

    assert "name: myapp.test" in content


def test_should_track_each_file_when_creating_commands(
    configurator: CursorConfigurator, tracker: Mock, project: Project
) -> None:
    commands = [
        Command(name="init", description="Initialize", prompt="Initialize"),
        Command(name="build", description="Build", prompt="Build"),
    ]

    configurator.commands(commands)

    assert tracker.track.call_count == 2
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("init.md" in str(f) for f in tracked_files)
    assert any("build.md" in str(f) for f in tracked_files)


def test_should_filter_custom_metadata_when_not_in_allowed_list(
    configurator: CursorConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Prompt", metadata={"custom_field": "custom_value"})]

    configurator.commands(commands)

    file = Path(project.dir) / ".cursorrules/commands/test.md"
    content = file.read_text()

    assert "custom_field" not in content


def test_should_return_early_when_no_rules_provided(configurator: CursorConfigurator, tracker: Mock) -> None:
    configurator.rules([], RuleMode.MERGED)

    tracker.track.assert_not_called()


def test_should_create_single_file_when_using_merged_mode(configurator: CursorConfigurator, project: Project) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".cursorrules/rules.md"
    assert file.exists()


def test_should_include_project_name_in_header_when_using_merged_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".cursorrules/rules.md"
    content = file.read_text()

    assert "# test-project guidelines" in content


def test_should_include_all_rule_descriptions_as_headers_when_using_merged_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing Guidelines", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".cursorrules/rules.md"
    content = file.read_text()

    assert "## Code Style" in content
    assert "## Testing Guidelines" in content


def test_should_include_all_rule_prompts_when_using_merged_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black formatter"),
        Rule(name="testing", description="Testing", prompt="Write comprehensive tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".cursorrules/rules.md"
    content = file.read_text()

    assert "Use Black formatter" in content
    assert "Write comprehensive tests" in content


def test_should_track_created_file_when_using_merged_mode(
    configurator: CursorConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    tracker.track.assert_called_once()
    assert str(Path(".cursorrules") / "rules.md") in str(tracker.track.call_args[0][0])


def test_should_create_rules_directory_when_using_separate_mode_and_directory_does_not_exist(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    rules_dir = Path(project.dir) / ".cursorrules/rules"
    assert rules_dir.exists()
    assert rules_dir.is_dir()


def test_should_create_file_for_each_rule_when_using_separate_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    style_file = Path(project.dir) / ".cursorrules/rules/style.md"
    testing_file = Path(project.dir) / ".cursorrules/rules/testing.md"

    assert style_file.exists()
    assert testing_file.exists()


def test_should_write_prompt_to_file_body_when_using_separate_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Style", prompt="Use Black formatter for all code")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".cursorrules/rules/style.md"
    content = file.read_text()

    assert "Use Black formatter for all code" in content


def test_should_include_description_in_frontmatter_when_using_separate_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Code Style Guidelines", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".cursorrules/rules/style.md"
    content = file.read_text()

    assert "description: Code Style Guidelines" in content


def test_should_apply_namespace_to_filename_when_using_separate_mode_with_namespace(
    agent: Agent,
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = CursorConfigurator(
        agent,
        project_with_namespace,
        tracker,
        markdown_generator,
        mcp_server_generator,
        assets_manager,
    )
    rules = [Rule(name="style", description="Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project_with_namespace.dir) / ".cursorrules/rules/myapp.style.md"
    assert file.exists()


def test_should_track_each_file_when_using_separate_mode(
    configurator: CursorConfigurator, tracker: Mock, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    assert tracker.track.call_count == 2
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("style.md" in str(f) for f in tracked_files)
    assert any("testing.md" in str(f) for f in tracked_files)


def test_should_filter_metadata_to_allowed_fields_when_using_separate_mode(
    configurator: CursorConfigurator, project: Project
) -> None:
    rules = [
        Rule(
            name="style",
            description="Style",
            prompt="Use Black",
            metadata={
                "alwaysApply": True,
                "globs": ["**/*.py"],
                "forbidden_field": "should_not_appear",
            },
        )
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project.dir) / ".cursorrules/rules/style.md"
    content = file.read_text()

    assert "alwaysApply: true" in content
    assert "globs:" in content
    assert "forbidden_field" not in content


def test_should_return_early_when_no_mcp_servers_provided(configurator: CursorConfigurator, tracker: Mock) -> None:
    configurator.mcp_servers([])

    tracker.track.assert_not_called()


def test_should_create_json_file_when_processing_mcp_servers(
    configurator: CursorConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="node", args=["server.js"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".cursorrules/mcp.json"
    assert file.exists()


def test_should_write_valid_json_when_processing_mcp_servers(configurator: CursorConfigurator, project: Path) -> None:
    servers = [StdioMCPServer(name="test-server", command="node", args=["server.js"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".cursorrules/mcp.json"
    with open(file) as f:
        data = json.load(f)

    assert "mcpServers" in data
    assert isinstance(data["mcpServers"], dict)


def test_should_include_server_configuration_without_name_field_when_processing_mcp_servers(
    configurator: CursorConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="node", args=["server.js"], env={"DEBUG": "true"})]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".cursorrules/mcp.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcpServers"]["test-server"]
    assert server_config["command"] == "node"
    assert server_config["args"] == ["server.js"]
    assert server_config["env"] == {"DEBUG": "true"}
    assert "name" not in server_config


def test_should_handle_multiple_servers_when_processing_mcp_servers(
    configurator: CursorConfigurator, project: Project
) -> None:
    servers = [
        StdioMCPServer(name="server1", command="node", args=["server1.js"]),
        StdioMCPServer(name="server2", command="python", args=["server2.py"]),
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".cursorrules/mcp.json"
    with open(file) as f:
        data = json.load(f)

    assert "server1" in data["mcpServers"]
    assert "server2" in data["mcpServers"]
    assert data["mcpServers"]["server1"]["command"] == "node"
    assert data["mcpServers"]["server2"]["command"] == "python"


def test_should_handle_http_servers_when_processing_mcp_servers(
    configurator: CursorConfigurator, project: Project
) -> None:
    servers = [HttpMCPServer(name="http-server", url="https://example.com", headers={"Authorization": "Bearer token"})]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / ".cursorrules/mcp.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcpServers"]["http-server"]
    assert server_config["url"] == "https://example.com"
    assert server_config["headers"] == {"Authorization": "Bearer token"}
    assert server_config["type"] == "http"


def test_should_track_created_file_when_processing_mcp_servers(
    configurator: CursorConfigurator, tracker: Mock, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="node")]

    configurator.mcp_servers(servers)

    tracker.track.assert_called_once()
    assert str(Path(".cursorrules") / "mcp.json") in str(tracker.track.call_args[0][0])


def test_should_create_mcp_directory_when_it_does_not_exist(configurator: CursorConfigurator, project: Project) -> None:
    servers = [StdioMCPServer(name="test-server", command="node")]

    configurator.mcp_servers(servers)

    mcp_dir = Path(project.dir) / ".cursorrules"
    assert mcp_dir.exists()
    assert mcp_dir.is_dir()


def test_should_delegate_asset_copying_to_assets_manager(
    configurator: CursorConfigurator, project: Project, tmp_path: Path
) -> None:
    """Test that assets() delegates to AssetsManager with correct paths."""
    # Mock the assets_manager
    configurator.assets_manager = Mock()

    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    assets = [str(source_file)]

    configurator.assets(assets)

    # Verify it calls assets_manager with correct arguments
    expected_source_base = Path(project.dir) / ".charlie" / "assets"
    expected_dest_base = Path(tmp_path / ".cursorrules") / "assets"

    configurator.assets_manager.copy_assets.assert_called_once_with(assets, expected_source_base, expected_dest_base)


def test_should_not_call_assets_manager_when_no_assets(
    configurator: CursorConfigurator,
) -> None:
    """Test that assets() returns early when assets list is empty."""
    configurator.assets_manager = Mock()

    configurator.assets([])

    configurator.assets_manager.copy_assets.assert_not_called()


def test_should_write_patterns_to_cursorignore_when_ignore_file_called(
    configurator: CursorConfigurator, project: Project
) -> None:
    patterns = [".charlie", "*.log", ".env", "secrets/"]

    configurator.ignore_file(patterns)

    ignore_file = Path(project.dir) / ".cursorignore"
    content = ignore_file.read_text()
    assert ".charlie" in content
    assert "*.log" in content
    assert ".env" in content
    assert "secrets/" in content


def test_should_write_all_provided_patterns_when_ignore_file_called(
    configurator: CursorConfigurator, project: Project
) -> None:
    patterns = [".charlie", "*.log"]

    configurator.ignore_file(patterns)

    ignore_file = Path(project.dir) / ".cursorignore"
    content = ignore_file.read_text()
    lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
    assert ".charlie" in lines
    assert "*.log" in lines


def test_should_preserve_pattern_order_when_writing_ignore_file(
    configurator: CursorConfigurator, project: Project
) -> None:
    patterns = [".charlie", "first.log", "second.log", "third.log"]

    configurator.ignore_file(patterns)

    ignore_file = Path(project.dir) / ".cursorignore"
    content = ignore_file.read_text()
    lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
    assert lines[0] == ".charlie"
    assert lines[1] == "first.log"
    assert lines[2] == "second.log"
    assert lines[3] == "third.log"


def test_should_create_parent_directory_when_ignore_file_path_does_not_exist(
    configurator: CursorConfigurator, project: Project
) -> None:
    patterns = ["*.log"]

    configurator.ignore_file(patterns)

    ignore_file = Path(project.dir) / ".cursorignore"
    assert ignore_file.exists()
    assert ignore_file.parent.exists()


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
    configurator = CursorConfigurator(
        agent_without_ignore, project, tracker, markdown_generator, mcp_server_generator, assets_manager
    )

    configurator.ignore_file(["*.log"])

    ignore_file = Path(project.dir) / ".cursorignore"
    assert not ignore_file.exists()


def test_should_track_file_generation_when_ignore_file_created(
    configurator: CursorConfigurator, project: Project, tracker: Mock
) -> None:
    patterns = ["*.log"]

    configurator.ignore_file(patterns)

    tracker.track.assert_called()
    call_args = tracker.track.call_args[0][0]
    assert "Generated ignore file" in call_args
