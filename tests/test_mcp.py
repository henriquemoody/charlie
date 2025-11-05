"""Tests for MCP server configuration generator."""

import json
import pytest
from pathlib import Path

from charlie.mcp import generate_mcp_config, _command_to_tool_schema, _server_to_mcp_config
from charlie.schema import CharlieConfig, ProjectConfig, MCPServer, Command, CommandScripts


def test_command_to_tool_schema():
    """Test converting command to MCP tool schema."""
    command = Command(
        name="init",
        description="Initialize feature",
        prompt="Test",
        scripts=CommandScripts(sh="init.sh"),
    )

    schema = _command_to_tool_schema(command, "myapp")

    assert schema["name"] == "myapp_init"
    assert schema["description"] == "Initialize feature"
    assert "inputSchema" in schema
    assert schema["inputSchema"]["type"] == "object"
    assert "input" in schema["inputSchema"]["properties"]


def test_server_to_mcp_config_basic():
    """Test converting server to MCP config."""
    server = MCPServer(name="test-server", command="node", args=["server.js"])

    commands = [
        Command(
            name="test",
            description="Test",
            prompt="Test",
            scripts=CommandScripts(sh="test.sh"),
        )
    ]

    config = _server_to_mcp_config(server, commands, "myapp")

    assert config["command"] == "node"
    assert config["args"] == ["server.js"]
    assert "capabilities" in config
    assert config["capabilities"]["tools"]["enabled"] is True
    assert len(config["capabilities"]["tools"]["list"]) == 1


def test_server_to_mcp_config_with_env():
    """Test server config with environment variables."""
    server = MCPServer(
        name="test-server",
        command="node",
        args=["server.js"],
        env={"DEBUG": "true", "PORT": "3000"},
    )

    config = _server_to_mcp_config(server, [], "myapp")

    assert "env" in config
    assert config["env"]["DEBUG"] == "true"
    assert config["env"]["PORT"] == "3000"


def test_generate_mcp_config(tmp_path):
    """Test generating complete MCP configuration file."""
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(name="server1", command="node", args=["server1.js"]),
            MCPServer(
                name="server2", command="python", args=["-m", "server2"], env={"DEBUG": "1"}
            ),
        ],
        commands=[
            Command(
                name="init",
                description="Initialize",
                prompt="Init",
                scripts=CommandScripts(sh="init.sh"),
            )
        ],
    )

    output_file = generate_mcp_config(config, str(tmp_path))

    # Check file was created
    assert Path(output_file).exists()

    # Check file content
    with open(output_file, "r") as f:
        mcp_config = json.load(f)

    assert "mcpServers" in mcp_config
    assert len(mcp_config["mcpServers"]) == 2
    assert "server1" in mcp_config["mcpServers"]
    assert "server2" in mcp_config["mcpServers"]

    # Check server1 config
    server1_config = mcp_config["mcpServers"]["server1"]
    assert server1_config["command"] == "node"
    assert server1_config["args"] == ["server1.js"]
    assert "capabilities" in server1_config

    # Check server2 has env
    server2_config = mcp_config["mcpServers"]["server2"]
    assert server2_config["env"]["DEBUG"] == "1"


def test_generate_mcp_config_no_servers():
    """Test that generating config without servers raises ValueError."""
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[],  # Empty list
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    with pytest.raises(ValueError, match="No MCP servers defined"):
        generate_mcp_config(config, "/tmp")


def test_generate_mcp_config_multiple_commands(tmp_path):
    """Test MCP config with multiple commands as tools."""
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"])],
        commands=[
            Command(
                name="init",
                description="Initialize",
                prompt="Init",
                scripts=CommandScripts(sh="init.sh"),
            ),
            Command(
                name="plan",
                description="Plan",
                prompt="Plan",
                scripts=CommandScripts(sh="plan.sh"),
            ),
        ],
    )

    output_file = generate_mcp_config(config, str(tmp_path))

    with open(output_file, "r") as f:
        mcp_config = json.load(f)

    tools = mcp_config["mcpServers"]["server"]["capabilities"]["tools"]["list"]
    assert len(tools) == 2
    assert tools[0]["name"] == "test_init"
    assert tools[1]["name"] == "test_plan"


def test_mcp_config_json_formatting(tmp_path):
    """Test that generated JSON is properly formatted."""
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"])],
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    output_file = generate_mcp_config(config, str(tmp_path))

    # Check that file has proper indentation and trailing newline
    content = Path(output_file).read_text()
    assert content.endswith("\n")
    assert "  " in content  # Has indentation

    # Should be valid JSON
    json.loads(content)

