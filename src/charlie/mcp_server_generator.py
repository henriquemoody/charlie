import json
from pathlib import Path

from charlie.schema import MCPServer
from charlie.tracker import Tracker


class MCPServerGenerator:
    def __init__(self, tracker: Tracker):
        self.tracker = tracker

    def generate(self, file: Path, mcp_servers: list[MCPServer]) -> None:
        if not mcp_servers:
            return

        file.parent.mkdir(parents=True, exist_ok=True)

        existing_servers: dict[str, object] = {}
        if file.exists():
            try:
                with open(file, encoding="utf-8") as open_file:
                    existing_config = json.load(open_file)
                    existing_servers = existing_config.get("mcpServers", {})
            except (json.JSONDecodeError, KeyError):
                existing_servers = {}

        for mcp_server in mcp_servers:
            server = mcp_server.model_dump(mode="json", exclude={"name"})
            is_update = mcp_server.name in existing_servers
            existing_servers[mcp_server.name] = server

            action = "Updated" if is_update else "Added"
            self.tracker.track(f"{action} MCP server '{mcp_server.name}' in {file}")

        with open(file, "w", encoding="utf-8") as open_file:
            json.dump({"mcpServers": existing_servers}, open_file, indent=2)
            open_file.write("\n")
