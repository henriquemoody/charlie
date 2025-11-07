import json
from pathlib import Path
from typing import Any

from charlie.schema import AgentSpec, CharlieConfig, Command, MCPServer
from charlie.utils import PlaceholderTransformer


def _command_to_tool_schema(command: Command, command_prefix: str | None) -> dict[str, Any]:
    name = f"{command_prefix}_{command.name}" if command_prefix else command.name
    return {
        "name": name,
        "description": command.description,
        "inputSchema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Command input"}},
            "required": ["input"],
        },
    }


def _server_to_mcp_config(
    server: MCPServer,
    commands: list[Command],
    command_prefix: str | None,
    transformer: PlaceholderTransformer | None = None,
) -> dict[str, Any]:
    # Transform placeholders in command and args if transformer is provided
    command = server.command
    args = server.args.copy() if server.args else []

    if transformer:
        command = transformer.transform_path_placeholders(command)
        command = transformer.transform_env_placeholders(command)
        args = [transformer.transform_env_placeholders(transformer.transform_path_placeholders(arg)) for arg in args]

    config: dict[str, Any] = {"command": command, "args": args}

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


def generate_mcp_config(
    config: CharlieConfig,
    agent_name: str,
    output_dir: str,
    agent_spec: AgentSpec | None = None,
    root_dir: str = ".",
) -> str:
    if not config.mcp_servers:
        raise ValueError("No MCP servers defined in configuration")

    # Only require command_prefix if there are commands to expose
    command_prefix = config.project.command_prefix if config.project else None
    mcp_config: dict[str, Any] = {"mcpServers": {}}

    # Create transformer if agent_spec is provided
    transformer = PlaceholderTransformer(agent_spec, root_dir) if agent_spec else None

    for server in config.mcp_servers:
        # Filter commands based on what this server should expose
        server_commands: list[Command] = []
        if server.commands:
            # Only include commands that are specified in the server's commands list
            command_dict = {cmd.name: cmd for cmd in config.commands}
            server_commands = [command_dict[cmd_name] for cmd_name in server.commands if cmd_name in command_dict]

        server_config = _server_to_mcp_config(server, server_commands, command_prefix, transformer)
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
