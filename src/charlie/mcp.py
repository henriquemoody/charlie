import json
from pathlib import Path
from typing import Any

from charlie.schema import CharlieConfig, Command, MCPServer


def _command_to_tool_schema(command: Command, command_prefix: str) -> dict[str, Any]:
    return {
        "name": f"{command_prefix}_{command.name}",
        "description": command.description,
        "inputSchema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Command input"}},
            "required": ["input"],
        },
    }


def _server_to_mcp_config(server: MCPServer, commands: list[Command], command_prefix: str) -> dict[str, Any]:
    config: dict[str, Any] = {"command": server.command, "args": server.args}

    if server.env:
        config["env"] = server.env

    if commands:
        config["capabilities"] = {
            "tools": {
                "enabled": True,
                "list": [_command_to_tool_schema(cmd, command_prefix) for cmd in commands],
            }
        }

    return config


def generate_mcp_config(config: CharlieConfig, agent_name: str, output_dir: str) -> str:
    if not config.mcp_servers:
        raise ValueError("No MCP servers defined in configuration")

    if not config.project or not config.project.command_prefix:
        raise ValueError("Project command_prefix is required for MCP config generation")

    mcp_config: dict[str, Any] = {"mcpServers": {}}

    for server in config.mcp_servers:
        server_config = _server_to_mcp_config(server, config.commands, config.project.command_prefix)
        mcp_config["mcpServers"][server.name] = server_config

    if agent_name == "cursor":
        output_path = Path(output_dir) / ".cursor" / "mcp.json"
    else:
        output_path = Path(output_dir) / "mcp-config.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=2)
        f.write("\n")

    return str(output_path)
