import json
from pathlib import Path

import pytest

from charlie.agents.registry import get_agent_spec
from charlie.mcp import _command_to_tool_schema, _server_to_mcp_config, generate_mcp_config
from charlie.schema import CharlieConfig, Command, CommandScripts, MCPServer, ProjectConfig


def test_command_to_tool_schema_converts_command_to_mcp_tool_format() -> None:
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


def test_server_to_mcp_config_basic_conversion_with_command_and_args() -> None:
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


def test_server_to_mcp_config_with_env() -> None:
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


def test_generate_mcp_config(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(name="server1", command="node", args=["server1.js"], commands=["init"]),
            MCPServer(name="server2", command="python", args=["-m", "server2"], env={"DEBUG": "1"}, commands=["init"]),
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

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    # Check file was created
    assert Path(output_file).exists()

    # Check file content
    with open(output_file) as f:
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


def test_generate_mcp_config_no_servers() -> None:
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
        generate_mcp_config(config, "cursor", "/tmp")


def test_generate_mcp_config_multiple_commands(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"], commands=["init", "plan"])],
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

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    with open(output_file) as f:
        mcp_config = json.load(f)

    tools = mcp_config["mcpServers"]["server"]["capabilities"]["tools"]["list"]
    assert len(tools) == 2
    assert tools[0]["name"] == "test_init"
    assert tools[1]["name"] == "test_plan"


def test_mcp_config_json_formatting(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"], commands=["test"])],
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    # Check that file has proper indentation and trailing newline
    content = Path(output_file).read_text()
    assert content.endswith("\n")
    assert "  " in content  # Has indentation

    # Should be valid JSON
    json.loads(content)


def test_generate_mcp_config_cursor_agent(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"], commands=["test"])],
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("cursor")
    output_file = generate_mcp_config(config, "cursor", str(tmp_path), agent_spec)

    # Check file was created at .cursor/mcp.json
    assert Path(output_file).exists()
    assert output_file == str(tmp_path / ".cursor" / "mcp.json")

    # Verify content is valid
    with open(output_file) as f:
        mcp_config = json.load(f)

    assert "mcpServers" in mcp_config
    assert "server" in mcp_config["mcpServers"]


def test_generate_mcp_config_default_location(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"], commands=["test"])],
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    # Test with no agent specified
    output_file = generate_mcp_config(config, "opencode", str(tmp_path))
    assert Path(output_file).exists()
    assert output_file == str(tmp_path / "mcp-config.json")

    # Test with claude agent
    output_file2 = generate_mcp_config(config, "claude", str(tmp_path / "claude-test"))
    assert Path(output_file2).exists()
    assert output_file2 == str(tmp_path / "claude-test" / "mcp-config.json")


def test_generate_mcp_config_without_command_prefix(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test"),  # No command_prefix
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"])],
        commands=[],  # No commands
    )

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    # Check file was created
    assert Path(output_file).exists()

    # Check file content
    with open(output_file) as f:
        mcp_config = json.load(f)

    assert "mcpServers" in mcp_config
    assert "server" in mcp_config["mcpServers"]
    assert mcp_config["mcpServers"]["server"]["command"] == "node"
    assert mcp_config["mcpServers"]["server"]["args"] == ["server.js"]


def test_mcp_server_transforms_env_placeholders(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("SERVER_PORT", "8080")

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(
                name="api-server",
                command="node",
                args=["server.js", "--api-key={{env:API_KEY}}", "--port={{env:SERVER_PORT}}"],
            )
        ],
        commands=[],
    )

    agent_spec = get_agent_spec("cursor")
    output_file = generate_mcp_config(config, "cursor", str(tmp_path), agent_spec, str(tmp_path))

    assert Path(output_file).exists()

    with open(output_file) as f:
        mcp_config = json.load(f)

    server_config = mcp_config["mcpServers"]["api-server"]
    assert server_config["command"] == "node"
    assert server_config["args"] == ["server.js", "--api-key=secret123", "--port=8080"]


def test_mcp_server_transforms_path_and_env_placeholders(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", "/var/data")

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(
                name="data-server",
                command="python",
                args=["{{root}}/server.py", "--data-dir={{env:DATA_DIR}}"],
            )
        ],
        commands=[],
    )

    agent_spec = get_agent_spec("cursor")
    output_file = generate_mcp_config(config, "cursor", str(tmp_path), agent_spec, str(tmp_path))

    with open(output_file) as f:
        mcp_config = json.load(f)

    server_config = mcp_config["mcpServers"]["data-server"]
    assert server_config["args"] == [f"{tmp_path}/server.py", "--data-dir=/var/data"]


def test_generate_mcp_config_without_command_prefix_no_project(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=None,  # No project config at all
        mcp_servers=[MCPServer(name="server", command="node", args=["server.js"])],
        commands=[],  # No commands
    )

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    # Check file was created
    assert Path(output_file).exists()

    # Check file content
    with open(output_file) as f:
        mcp_config = json.load(f)

    assert "mcpServers" in mcp_config
    assert "server" in mcp_config["mcpServers"]


def test_mcp_server_with_specific_commands_exposes_only_those_commands(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(
                name="server1",
                command="node",
                args=["server1.js"],
                commands=["init"],  # Only expose init command
            ),
            MCPServer(
                name="server2",
                command="python",
                args=["-m", "server2"],
                commands=["plan", "deploy"],  # Only expose plan and deploy
            ),
        ],
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
            Command(
                name="deploy",
                description="Deploy",
                prompt="Deploy",
                scripts=CommandScripts(sh="deploy.sh"),
            ),
        ],
    )

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    with open(output_file) as f:
        mcp_config = json.load(f)

    # server1 should only have init command
    server1_tools = mcp_config["mcpServers"]["server1"]["capabilities"]["tools"]["list"]
    assert len(server1_tools) == 1
    assert server1_tools[0]["name"] == "test_init"

    # server2 should only have plan and deploy commands
    server2_tools = mcp_config["mcpServers"]["server2"]["capabilities"]["tools"]["list"]
    assert len(server2_tools) == 2
    assert server2_tools[0]["name"] == "test_plan"
    assert server2_tools[1]["name"] == "test_deploy"


def test_mcp_server_without_commands_field_exposes_no_commands(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        mcp_servers=[
            MCPServer(
                name="server",
                command="node",
                args=["server.js"],
                # No commands field specified
            ),
        ],
        commands=[
            Command(
                name="init",
                description="Initialize",
                prompt="Init",
                scripts=CommandScripts(sh="init.sh"),
            ),
        ],
    )

    output_file = generate_mcp_config(config, "cursor", str(tmp_path))

    with open(output_file) as f:
        mcp_config = json.load(f)

    # Server should not have capabilities when no commands are specified
    server_config = mcp_config["mcpServers"]["server"]
    assert "capabilities" not in server_config
