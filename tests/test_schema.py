import pytest
from pydantic import ValidationError

from charlie.schema import (
    CharlieConfig,
    Command,
    CommandScripts,
    MCPServer,
    ProjectConfig,
    RulesConfig,
    RulesSection,
)


def test_project_config_valid() -> None:
    config = ProjectConfig(name="test-project", command_prefix="test")
    assert config.name == "test-project"
    assert config.command_prefix == "test"


def test_mcp_server_valid() -> None:
    server = MCPServer(
        name="test-server",
        command="node",
        args=["server.js"],
        env={"DEBUG": "true"},
    )
    assert server.name == "test-server"
    assert server.command == "node"
    assert server.args == ["server.js"]
    assert server.env == {"DEBUG": "true"}


def test_mcp_server_defaults() -> None:
    server = MCPServer(name="test-server", command="node")
    assert server.args == []
    assert server.env == {}
    assert server.commands is None
    assert server.config is None


def test_mcp_server_with_extra_fields() -> None:
    server = MCPServer(
        name="test-server",
        command="node",
        commands=["init", "build"],
        config={"timeout": 30000},
        custom_field="custom_value",  # Extra field
    )
    assert server.commands == ["init", "build"]
    assert server.config == {"timeout": 30000}
    # Verify extra field is preserved
    server_dict = server.model_dump()
    assert server_dict["custom_field"] == "custom_value"


def test_rules_config_defaults() -> None:
    rules = RulesConfig()
    assert rules.title == "Development Guidelines"
    assert rules.include_commands is True
    assert rules.include_tech_stack is True
    assert rules.preserve_manual is True
    assert rules.sections is None


def test_rules_section_valid() -> None:
    section = RulesSection(
        title="Code Style",
        content="Use Black for formatting",
        order=1,
    )
    assert section.title == "Code Style"
    assert section.content == "Use Black for formatting"
    assert section.order == 1


def test_rules_section_with_agent_fields() -> None:
    section = RulesSection(
        title="Python Style",
        content="Type hints required",
        order=2,
        alwaysApply=True,  # Cursor-specific
        globs=["**/*.py"],  # Cursor-specific
        priority="high",  # Windsurf-specific
    )
    assert section.title == "Python Style"
    # Verify pass-through fields are preserved
    section_dict = section.model_dump()
    assert section_dict["alwaysApply"] is True
    assert section_dict["globs"] == ["**/*.py"]
    assert section_dict["priority"] == "high"


def test_command_scripts_valid() -> None:
    scripts = CommandScripts(sh="script.sh", ps="script.ps1")
    assert scripts.sh == "script.sh"
    assert scripts.ps == "script.ps1"


def test_command_valid() -> None:
    cmd = Command(
        name="test",
        description="Test command",
        prompt="Test prompt",
        scripts=CommandScripts(sh="test.sh"),
    )
    assert cmd.name == "test"
    assert cmd.description == "Test command"
    assert cmd.prompt == "Test prompt"
    assert cmd.scripts.sh == "test.sh"


def test_command_with_agent_fields() -> None:
    command = Command(
        name="commit",
        description="Git commit",
        prompt="Create commit",
        scripts=CommandScripts(sh="commit.sh"),
        allowed_tools=["Bash(git add:*)", "Bash(git commit:*)"],  # Claude-specific
        tags=["git", "vcs"],
        category="source-control",
    )
    assert command.name == "commit"
    # Verify pass-through fields are preserved
    command_dict = command.model_dump()
    assert command_dict["allowed_tools"] == ["Bash(git add:*)", "Bash(git commit:*)"]
    assert command_dict["tags"] == ["git", "vcs"]
    assert command_dict["category"] == "source-control"


def test_command_no_scripts_fails() -> None:
    with pytest.raises(ValidationError):
        Command(
            name="test",
            description="Test command",
            prompt="Test prompt",
            scripts=CommandScripts(),
        )


def test_charlie_config_valid() -> None:
    config_data = {
        "version": "1.0",
        "project": {"name": "test-project", "command_prefix": "test"},
        "commands": [
            {
                "name": "init",
                "description": "Initialize",
                "prompt": "Test prompt",
                "scripts": {"sh": "init.sh"},
            }
        ],
    }
    config = CharlieConfig(**config_data)
    assert config.version == "1.0"
    assert config.project.name == "test-project"
    assert len(config.commands) == 1
    assert config.commands[0].name == "init"


def test_charlie_config_with_mcp() -> None:
    config_data = {
        "version": "1.0",
        "project": {"name": "test", "command_prefix": "test"},
        "mcp_servers": [{"name": "server1", "command": "node", "args": ["server.js"]}],
        "commands": [
            {
                "name": "test",
                "description": "Test",
                "prompt": "Prompt",
                "scripts": {"sh": "test.sh"},
            }
        ],
    }
    config = CharlieConfig(**config_data)
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "server1"


def test_charlie_config_invalid_version() -> None:
    config_data = {
        "version": "2.0",
        "project": {"name": "test", "command_prefix": "test"},
        "commands": [
            {
                "name": "test",
                "description": "Test",
                "prompt": "Prompt",
                "scripts": {"sh": "test.sh"},
            }
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        CharlieConfig(**config_data)
    assert "version" in str(exc_info.value)


def test_charlie_config_duplicate_commands() -> None:
    config_data = {
        "version": "1.0",
        "project": {"name": "test", "command_prefix": "test"},
        "commands": [
            {
                "name": "test",
                "description": "Test 1",
                "prompt": "Prompt 1",
                "scripts": {"sh": "test1.sh"},
            },
            {
                "name": "test",
                "description": "Test 2",
                "prompt": "Prompt 2",
                "scripts": {"sh": "test2.sh"},
            },
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        CharlieConfig(**config_data)
    assert "Duplicate command names" in str(exc_info.value)


def test_charlie_config_minimal() -> None:
    config = CharlieConfig(
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ]
    )
    assert config.version == "1.0"  # Default
    assert config.project is None  # Optional
    assert len(config.commands) == 1


def test_charlie_config_empty_commands() -> None:
    config_data = {
        "version": "1.0",
        "project": {"name": "test", "command_prefix": "test"},
        "commands": [],
    }
    config = CharlieConfig(**config_data)
    assert config.commands == []
