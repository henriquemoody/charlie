import json
import shutil
from pathlib import Path
from typing import Any, final

from charlie.assets_manager import AssetsManager
from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Command, HttpMCPServer, MCPServer, Project, Rule, Skill, StdioMCPServer, Subagent
from charlie.tracker import Tracker


@final
class OpencodeConfigurator(AgentConfigurator):
    COMMANDS_SHORTHAND_INJECTION = "$ARGUMENTS"
    SKILLS_DIR = ".opencode/skills"
    SKILLS_FILE = "SKILL.md"
    SUBAGENTS_DIR = ".opencode/agents"
    SUBAGENTS_EXTENSION = "md"
    MCP_FILE = "opencode.json"
    ASSETS_DIR = ".opencode/assets"

    __ALLOWED_SKILL_METADATA = [
        "description",
        "license",
        "compatibility",
        "metadata",
    ]
    __ALLOWED_SUBAGENT_METADATA = [
        "description",
        "tools",
        "model",
        "permission",
    ]

    def __init__(
        self,
        project: Project,
        tracker: Tracker,
        markdown_generator: MarkdownGenerator,
        mcp_server_generator: None,
        assets_manager: AssetsManager,
        short_name: str,
    ):
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator
        self.assets_manager = assets_manager
        self.short_name = short_name

    def placeholders(self) -> dict[str, str]:
        return {
            "agent_name": "OpenCode",
            "agent_shortname": self.short_name,
            "agent_dir": ".opencode",
            "commands_dir": self.SKILLS_DIR,
            "commands_shorthand_injection": self.COMMANDS_SHORTHAND_INJECTION,
            "rules_dir": "",
            "rules_file": "",
            "subagents_dir": self.SUBAGENTS_DIR,
            "skills_dir": self.SKILLS_DIR,
            "mcp_file": self.MCP_FILE,
            "assets_dir": self.ASSETS_DIR,
        }

    def commands(self, commands: list[Command]) -> None:
        for command in commands:
            self.__write_skill(
                name=command.name,
                description=command.description,
                prompt=command.prompt,
                metadata=command.metadata,
            )

    def rules(self, rules: list[Rule], mode: RuleMode) -> None:
        if rules:
            self.tracker.track("OpenCode does not support rules natively. Skipping...")

    def subagents(self, subagents: list[Subagent]) -> None:
        if not subagents:
            return

        subagents_dir = Path(self.project.dir) / self.SUBAGENTS_DIR
        subagents_dir.mkdir(parents=True, exist_ok=True)

        for subagent in subagents:
            name = subagent.name
            filename = f"{name}.{self.SUBAGENTS_EXTENSION}"
            if self.project.namespace is not None:
                name = f"{self.project.namespace}-{name}"
                filename = f"{self.project.namespace}-{filename}"

            subagent_file = subagents_dir / filename
            self.markdown_generator.generate(
                file=subagent_file,
                body=subagent.prompt,
                metadata={"name": name, "description": subagent.description, **subagent.metadata},
                allowed_metadata=["name", "description", *self.__ALLOWED_SUBAGENT_METADATA],
            )

            self.tracker.track(f"Created {subagent_file}")

    def skills(self, skills: list[Skill]) -> None:
        for skill in skills:
            self.__write_skill(
                name=skill.name,
                description=skill.description,
                prompt=skill.prompt,
                metadata=skill.metadata,
                files=skill.files,
            )

    def __write_skill(
        self,
        name: str,
        description: str,
        prompt: str,
        metadata: dict[str, Any],
        files: dict[str, str] | None = None,
    ) -> None:
        skills_dir = Path(self.project.dir) / self.SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)

        if self.project.namespace is not None:
            name = f"{self.project.namespace}-{name}"

        skill_dir = skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_file = skill_dir / self.SKILLS_FILE
        self.markdown_generator.generate(
            file=skill_file,
            body=prompt,
            metadata={**metadata, "name": name, "description": description},
            allowed_metadata=["name", *self.__ALLOWED_SKILL_METADATA],
        )

        self.tracker.track(f"Created {skill_file}")

        for relative_path, source_path in (files or {}).items():
            dest = skill_dir / relative_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest)
            self.tracker.track(f"Created {dest}")

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        if not mcp_servers:
            return

        file = Path(self.project.dir) / self.MCP_FILE

        config: dict[str, Any] = {}
        if file.exists():
            with open(file, encoding="utf-8") as f:
                config = json.load(f)

        if "$schema" not in config:
            config["$schema"] = "https://opencode.ai/config.json"

        if "mcp" not in config:
            config["mcp"] = {}

        for server in mcp_servers:
            if isinstance(server, StdioMCPServer):
                server_config: dict[str, Any] = {
                    "type": "local",
                    "command": [server.command] + (server.args or []),
                }
                if server.env:
                    server_config["environment"] = server.env
            elif isinstance(server, HttpMCPServer):
                server_config = {
                    "type": "remote",
                    "url": server.url,
                }
                if server.headers:
                    server_config["headers"] = server.headers
            else:
                continue

            config["mcp"][server.name] = server_config

        with open(file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        self.tracker.track(f"Created {file}")

    def assets(self, assets: list[str]) -> None:
        if not assets:
            return

        destination_base = Path(self.project.dir) / self.ASSETS_DIR
        self.assets_manager.copy_assets(assets, destination_base)

    def ignore_file(self, patterns: list[str]) -> None:
        if patterns:
            self.tracker.track("OpenCode does not support ignore files natively. Skipping...")
