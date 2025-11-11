import json
import shutil
from pathlib import Path
from typing import final

from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Agent, Command, MCPServer, Project, Rule
from charlie.tracker import Tracker


@final
class ClaudeConfigurator(AgentConfigurator):
    __ALLOWED_COMMAND_METADATA = ["description", "allowed-tools", "argument-hint", "model", "disable-model-invocation"]
    __ALLOWED_INSTRUCTION_METADATA = ["description"]

    def __init__(self, agent: Agent, project: Project, tracker: Tracker, markdown_generator: MarkdownGenerator):
        self.agent = agent
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator

    def commands(self, commands: list[Command]) -> None:
        commands_dir = Path(self.project.dir) / self.agent.commands_dir
        commands_dir.mkdir(parents=True, exist_ok=True)
        for command in commands:
            name = command.name
            filename = f"{name}.{self.agent.commands_extension}"
            if self.project.namespace is not None:
                filename = f"{self.project.namespace}-{filename}"

            command_file = commands_dir / filename
            self.markdown_generator.generate(
                file=command_file,
                body=command.prompt,
                metadata={"description": command.description, **command.metadata},
                allowed_metadata=self.__ALLOWED_COMMAND_METADATA,
            )

            self.tracker.track(f"Created {command_file}")

    def rules(self, rules: list[Rule], mode: RuleMode) -> None:
        if not rules:
            return

        rules_file = Path(self.project.dir) / self.agent.rules_file
        rules_file.parent.mkdir(parents=True, exist_ok=True)

        if mode == RuleMode.MERGED:
            body = f"# {self.project.name}\n\n"

            for rule in rules:
                body += f"## {rule.description}\n\n"
                body += f"{rule.prompt}\n\n"

            self.markdown_generator.generate(file=rules_file, body=body.rstrip())
            self.tracker.track(f"Created {rules_file}")
            return

        rules_dir = Path(self.project.dir) / self.agent.rules_dir
        rules_dir.mkdir(parents=True, exist_ok=True)

        body = f"# {self.project.name}\n\n"

        for rule in rules:
            filename = f"{rule.name}.{self.agent.rules_extension}"
            if self.project.namespace is not None:
                filename = f"{self.project.namespace}-{filename}"

            rule_file = rules_dir / filename
            self.markdown_generator.generate(
                file=rule_file,
                body=rule.prompt,
                metadata={"description": rule.description, **rule.metadata},
                allowed_metadata=self.__ALLOWED_INSTRUCTION_METADATA,
            )

            relative_path = f"{self.agent.rules_dir}/{filename}"
            body += f"## {rule.description}\n\n"
            body += f"@{relative_path}\n\n"

            self.tracker.track(f"Created {rule_file}")

        self.markdown_generator.generate(file=rules_file, body=body.rstrip())
        self.tracker.track(f"Created {rules_file}")

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        if not mcp_servers:
            return

        file = Path(self.project.dir) / Path(self.agent.mcp_file)
        file.parent.mkdir(parents=True, exist_ok=True)
        servers: dict[str, object] = {}

        for mcp_server in mcp_servers:
            server = mcp_server.__dict__.copy()
            del server["name"]
            servers[mcp_server.name] = server

        with open(file, "w", encoding="utf-8") as open_file:
            json.dump({"mcpServers": servers}, open_file, indent=2)
            open_file.write("\n")
            self.tracker.track(f"Created {file}")

    def assets(self, assets: list[str]) -> None:
        for asset in assets:
            asset_path = Path(asset)
            charlie_assets = Path(self.project.dir) / ".charlie" / "assets"
            relative_path = asset_path.relative_to(charlie_assets)
            destination = Path(self.agent.dir) / "assets" / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, destination)
            self.tracker.track(f"Created {asset}")
