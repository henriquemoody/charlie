import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.assets_manager import AssetsManager
from charlie.configurators.opencode_configurator import OpencodeConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Command, HttpMCPServer, Project, Rule, Skill, StdioMCPServer, Subagent


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
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> OpencodeConfigurator:
    return OpencodeConfigurator(project, tracker, markdown_generator, None, assets_manager, "opencode")


def test_should_create_skills_directory_when_generating_commands(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test command", prompt="Test prompt")]

    configurator.commands(commands)

    skills_dir = Path(project.dir) / ".opencode/skills"
    assert skills_dir.exists()
    assert skills_dir.is_dir()


def test_should_create_skill_file_when_processing_each_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix issue", prompt="Fix the issue"),
        Command(name="review-pr", description="Review PR", prompt="Review pull request"),
    ]

    configurator.commands(commands)

    fix_file = Path(project.dir) / ".opencode/skills/fix-issue/SKILL.md"
    review_file = Path(project.dir) / ".opencode/skills/review-pr/SKILL.md"

    assert fix_file.exists()
    assert review_file.exists()


def test_should_write_prompt_to_file_body_when_creating_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Test", prompt="Fix issue #$ARGUMENTS following our coding standards")]

    configurator.commands(commands)

    file = Path(project.dir) / ".opencode/skills/test/SKILL.md"
    content = file.read_text()

    assert "Fix issue #$ARGUMENTS following our coding standards" in content


def test_should_include_description_in_frontmatter_when_creating_command(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [Command(name="test", description="Fix a numbered issue", prompt="Fix issue")]

    configurator.commands(commands)

    file = Path(project.dir) / ".opencode/skills/test/SKILL.md"
    content = file.read_text()

    assert "description: Fix a numbered issue" in content


def test_should_include_license_in_frontmatter_when_specified(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            metadata={"license": "MIT"},
        )
    ]

    configurator.commands(commands)

    file = Path(project.dir) / ".opencode/skills/test/SKILL.md"
    content = file.read_text()

    assert "license: MIT" in content


def test_should_apply_namespace_prefix_to_directory_when_namespace_is_present(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        project_with_namespace,
        tracker,
        markdown_generator,
        None,
        assets_manager,
        "opencode",
    )
    commands = [Command(name="test", description="Test", prompt="Prompt")]

    configurator.commands(commands)

    file = Path(project_with_namespace.dir) / ".opencode/skills/myapp-test/SKILL.md"
    assert file.exists()


def test_should_track_each_file_when_creating_commands(
    configurator: OpencodeConfigurator, tracker: Mock, project: Project
) -> None:
    commands = [
        Command(name="fix-issue", description="Fix", prompt="Fix"),
        Command(name="review-pr", description="Review", prompt="Review"),
    ]

    configurator.commands(commands)

    assert tracker.track.call_count == 2
    tracked_files = [call[0][0] for call in tracker.track.call_args_list]
    assert any("fix-issue" in str(f) and "SKILL.md" in str(f) for f in tracked_files)
    assert any("review-pr" in str(f) and "SKILL.md" in str(f) for f in tracked_files)


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

    file = Path(project.dir) / ".opencode/skills/test/SKILL.md"
    content = file.read_text()

    assert "forbidden_field" not in content


def test_should_return_early_when_no_rules_provided(configurator: OpencodeConfigurator, tracker: Mock) -> None:
    configurator.rules([], RuleMode.MERGED)

    tracker.track.assert_not_called()


def test_should_create_merged_instructions_file_when_mode_is_merged(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project.dir) / ".opencode/instructions/instructions.md"
    assert file.exists()
    content = file.read_text()
    assert "Code Style" in content
    assert "Use Black" in content
    assert "Testing" in content
    assert "Write tests" in content


def test_should_create_separate_instruction_files_when_mode_is_separate(
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
    assert "Use Black" in style_file.read_text()
    assert "Write tests" in testing_file.read_text()


def test_should_register_instructions_in_opencode_json_when_rules_merged(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [Rule(name="style", description="Code Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    config_file = Path(project.dir) / "opencode.json"
    with open(config_file) as f:
        data = json.load(f)

    assert ".opencode/instructions/instructions.md" in data["instructions"]


def test_should_register_instructions_in_opencode_json_when_rules_separate(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    rules = [
        Rule(name="style", description="Code Style", prompt="Use Black"),
        Rule(name="testing", description="Testing", prompt="Write tests"),
    ]

    configurator.rules(rules, RuleMode.SEPARATE)

    config_file = Path(project.dir) / "opencode.json"
    with open(config_file) as f:
        data = json.load(f)

    assert ".opencode/instructions/style.md" in data["instructions"]
    assert ".opencode/instructions/testing.md" in data["instructions"]


def test_should_preserve_existing_instructions_when_adding_rules(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    config_file = Path(project.dir) / "opencode.json"
    existing_config = {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["CONTRIBUTING.md"],
    }
    with open(config_file, "w") as f:
        json.dump(existing_config, f)

    rules = [Rule(name="style", description="Code Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    with open(config_file) as f:
        data = json.load(f)

    assert "CONTRIBUTING.md" in data["instructions"]
    assert ".opencode/instructions/style.md" in data["instructions"]


def test_should_apply_namespace_prefix_to_merged_instructions_file(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        project_with_namespace,
        tracker,
        markdown_generator,
        None,
        assets_manager,
        "opencode",
    )
    rules = [Rule(name="style", description="Code Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.MERGED)

    file = Path(project_with_namespace.dir) / ".opencode/instructions/myapp-instructions.md"
    assert file.exists()


def test_should_apply_namespace_prefix_to_separate_instruction_files(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        project_with_namespace,
        tracker,
        markdown_generator,
        None,
        assets_manager,
        "opencode",
    )
    rules = [Rule(name="style", description="Code Style", prompt="Use Black")]

    configurator.rules(rules, RuleMode.SEPARATE)

    file = Path(project_with_namespace.dir) / ".opencode/instructions/myapp-style.md"
    assert file.exists()


def test_should_create_agents_directory_when_generating_subagents(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(name="test-agent", description="Test agent", prompt="Be helpful")
    ]

    configurator.subagents(subagents)

    agents_dir = Path(project.dir) / ".opencode/agents"
    assert agents_dir.exists()
    assert agents_dir.is_dir()


def test_should_create_agent_files_when_processing_subagents(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(name="reviewer", description="Code reviewer", prompt="Review code"),
        Subagent(name="planner", description="Task planner", prompt="Plan tasks"),
    ]

    configurator.subagents(subagents)

    reviewer_file = Path(project.dir) / ".opencode/agents/reviewer.md"
    planner_file = Path(project.dir) / ".opencode/agents/planner.md"

    assert reviewer_file.exists()
    assert planner_file.exists()


def test_should_include_name_in_frontmatter_when_creating_agent(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    subagents = [
        Subagent(name="test-agent", description="Test agent", prompt="Be helpful")
    ]

    configurator.subagents(subagents)

    file = Path(project.dir) / ".opencode/agents/test-agent.md"
    content = file.read_text()

    assert "name: test-agent" in content


def test_should_apply_namespace_prefix_when_processing_subagents_with_namespace(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        project_with_namespace,
        tracker,
        markdown_generator,
        None,
        assets_manager,
        "opencode",
    )
    subagents = [
        Subagent(name="reviewer", description="Code reviewer", prompt="Review code")
    ]

    configurator.subagents(subagents)

    file = Path(project_with_namespace.dir) / ".opencode/agents/myapp-reviewer.md"
    assert file.exists()


def test_should_create_skill_directory_when_processing_skills(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    skills = [Skill(name="debug", description="Debug tool", prompt="Debug the issue")]

    configurator.skills(skills)

    skill_file = Path(project.dir) / ".opencode/skills/debug/SKILL.md"
    assert skill_file.exists()


def test_should_include_description_in_frontmatter_when_creating_skill(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    skills = [Skill(name="debug", description="Debug tool", prompt="Debug the issue")]

    configurator.skills(skills)

    file = Path(project.dir) / ".opencode/skills/debug/SKILL.md"
    content = file.read_text()

    assert "description: Debug tool" in content


def test_should_apply_namespace_prefix_when_processing_skills_with_namespace(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> None:
    configurator = OpencodeConfigurator(
        project_with_namespace,
        tracker,
        markdown_generator,
        None,
        assets_manager,
        "opencode",
    )
    skills = [Skill(name="debug", description="Debug", prompt="Debug")]

    configurator.skills(skills)

    file = Path(project_with_namespace.dir) / ".opencode/skills/myapp-debug/SKILL.md"
    assert file.exists()


def test_should_copy_companion_files_when_skill_has_files(
    configurator: OpencodeConfigurator, project: Project, tmp_path: Path
) -> None:
    source_file = tmp_path / "source.txt"
    source_file.write_text("companion content")

    skills = [
        Skill(
            name="with-files",
            description="Skill with files",
            prompt="Do something",
            files={"data/config.txt": str(source_file)},
        )
    ]

    configurator.skills(skills)

    dest = Path(project.dir) / ".opencode/skills/with-files/data/config.txt"
    assert dest.exists()
    assert dest.read_text() == "companion content"


def test_should_return_early_when_no_mcp_servers_provided(configurator: OpencodeConfigurator, tracker: Mock) -> None:
    configurator.mcp_servers([])

    tracker.track.assert_not_called()


def test_should_create_opencode_json_when_processing_mcp_servers(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / "opencode.json"
    assert file.exists()


def test_should_write_valid_json_when_processing_mcp_servers(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    servers = [StdioMCPServer(name="test-server", command="npx", args=["-y", "test-server"])]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / "opencode.json"
    with open(file) as f:
        data = json.load(f)

    assert "$schema" in data
    assert "mcp" in data
    assert isinstance(data["mcp"], dict)


def test_should_use_local_type_for_stdio_servers(configurator: OpencodeConfigurator, project: Project) -> None:
    servers = [
        StdioMCPServer(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"},
        )
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / "opencode.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcp"]["github"]
    assert server_config["type"] == "local"
    assert server_config["command"] == ["npx", "-y", "@modelcontextprotocol/server-github"]
    assert server_config["environment"] == {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"}


def test_should_use_remote_type_for_http_servers(configurator: OpencodeConfigurator, project: Project) -> None:
    servers = [
        HttpMCPServer(name="api-server", url="https://api.example.com", headers={"Authorization": "Bearer token"})
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / "opencode.json"
    with open(file) as f:
        data = json.load(f)

    server_config = data["mcp"]["api-server"]
    assert server_config["type"] == "remote"
    assert server_config["url"] == "https://api.example.com"
    assert server_config["headers"] == {"Authorization": "Bearer token"}


def test_should_handle_multiple_servers_when_processing_mcp_servers(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    servers = [
        StdioMCPServer(name="github", command="npx", args=["-y", "github-server"]),
        HttpMCPServer(name="api", url="https://api.example.com"),
    ]

    configurator.mcp_servers(servers)

    file = Path(project.dir) / "opencode.json"
    with open(file) as f:
        data = json.load(f)

    assert "github" in data["mcp"]
    assert "api" in data["mcp"]
    assert data["mcp"]["github"]["type"] == "local"
    assert data["mcp"]["api"]["type"] == "remote"


def test_should_preserve_existing_config_when_adding_mcp_servers(
    configurator: OpencodeConfigurator, project: Project
) -> None:
    config_file = Path(project.dir) / "opencode.json"
    existing_config = {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["CONTRIBUTING.md"],
        "mcp": {"existing-server": {"type": "local", "command": ["cmd"]}},
    }
    with open(config_file, "w") as f:
        json.dump(existing_config, f)

    servers = [StdioMCPServer(name="new-server", command="npx")]
    configurator.mcp_servers(servers)

    with open(config_file) as f:
        data = json.load(f)

    assert data["instructions"] == ["CONTRIBUTING.md"]
    assert "existing-server" in data["mcp"]
    assert "new-server" in data["mcp"]


def test_should_return_early_when_no_assets(configurator: OpencodeConfigurator) -> None:
    configurator.assets_manager = Mock()

    configurator.assets([])

    configurator.assets_manager.copy_assets.assert_not_called()


def test_should_delegate_asset_copying_to_assets_manager(
    configurator: OpencodeConfigurator, project: Project, tmp_path: Path
) -> None:
    configurator.assets_manager = Mock()

    source_file = Path(project.dir) / ".charlie/assets/test.txt"
    assets = [str(source_file)]

    configurator.assets(assets)

    expected_dest_base = Path(project.dir) / ".opencode/assets"
    configurator.assets_manager.copy_assets.assert_called_once_with(assets, expected_dest_base)


def test_should_track_skip_message_when_ignore_patterns_provided(
    configurator: OpencodeConfigurator, tracker: Mock
) -> None:
    patterns = [".charlie", "*.log", ".env"]

    configurator.ignore_file(patterns)

    tracker.track.assert_called_once_with("OpenCode does not support ignore files natively. Skipping...")


def test_should_return_opencode_placeholders(configurator: OpencodeConfigurator) -> None:
    placeholders = configurator.placeholders()

    assert placeholders["agent_name"] == "OpenCode"
    assert placeholders["agent_shortname"] == "opencode"
    assert placeholders["agent_dir"] == ".opencode"
    assert placeholders["rules_dir"] == ".opencode/instructions"
    assert placeholders["skills_dir"] == ".opencode/skills"
    assert placeholders["subagents_dir"] == ".opencode/agents"
    assert placeholders["mcp_file"] == "opencode.json"
    assert placeholders["assets_dir"] == ".opencode/assets"
