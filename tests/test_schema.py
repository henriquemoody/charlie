"""Tests for schema validation."""

import pytest
from pydantic import ValidationError

from charlie.schema import (
    CharlieConfig,
    ProjectConfig,
    MCPServer,
    RulesConfig,
    Command,
    CommandScripts,
)


def test_project_config_valid():
    """Test valid project configuration."""
    config = ProjectConfig(name="test-project", command_prefix="test")
    assert config.name == "test-project"
    assert config.command_prefix == "test"


def test_mcp_server_valid():
    """Test valid MCP server configuration."""
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


def test_mcp_server_defaults():
    """Test MCP server with default values."""
    server = MCPServer(name="test-server", command="node")
    assert server.args == []
    assert server.env == {}


def test_rules_config_defaults():
    """Test rules configuration with default values."""
    rules = RulesConfig()
    assert rules.title == "Development Guidelines"
    assert rules.include_commands is True
    assert rules.include_tech_stack is True
    assert rules.preserve_manual is True


def test_command_scripts_valid():
    """Test valid command scripts."""
    scripts = CommandScripts(sh="script.sh", ps="script.ps1")
    assert scripts.sh == "script.sh"
    assert scripts.ps == "script.ps1"


def test_command_valid():
    """Test valid command configuration."""
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


def test_command_no_scripts_fails():
    """Test command without scripts fails validation."""
    with pytest.raises(ValidationError):
        Command(
            name="test",
            description="Test command",
            prompt="Test prompt",
            scripts=CommandScripts(),
        )


def test_charlie_config_valid():
    """Test valid full charlie configuration."""
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


def test_charlie_config_with_mcp():
    """Test configuration with MCP servers."""
    config_data = {
        "version": "1.0",
        "project": {"name": "test", "command_prefix": "test"},
        "mcp_servers": [
            {"name": "server1", "command": "node", "args": ["server.js"]}
        ],
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


def test_charlie_config_invalid_version():
    """Test configuration with invalid version fails."""
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


def test_charlie_config_duplicate_commands():
    """Test configuration with duplicate command names fails."""
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


def test_charlie_config_no_commands():
    """Test configuration without commands fails."""
    config_data = {
        "version": "1.0",
        "project": {"name": "test", "command_prefix": "test"},
        "commands": [],
    }
    with pytest.raises(ValidationError):
        CharlieConfig(**config_data)

