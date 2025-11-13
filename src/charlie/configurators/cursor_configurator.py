import shutil
from pathlib import Path
from typing import final

from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Agent, Command, MCPServer, Project, Rule
from charlie.tracker import Tracker


@final
class CursorConfigurator(AgentConfigurator):
    __ALLOWED_COMMAND_METADATA = ["name", "description"]
    __ALLOWED_INSTRUCTION_METADATA = ["description", "alwaysApply", "globs"]

    def __init__(
        self,
        agent: Agent,
        project: Project,
        tracker: Tracker,
        markdown_generator: MarkdownGenerator,
        mcp_server_generator: MCPServerGenerator,
    ):
        self.agent = agent
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator
        self.mcp_server_generator = mcp_server_generator

    def commands(self, commands: list[Command]) -> None:
        commands_dir = Path(self.project.dir) / self.agent.commands_dir
        commands_dir.mkdir(parents=True, exist_ok=True)
        for command in commands:
            name = command.name
            filename = f"{name}.{self.agent.commands_extension}"
            if self.project.namespace is not None:
                name = f"{self.project.namespace}.{name}"
                filename = f"{self.project.namespace}.{filename}"

            command_file = commands_dir / filename
            self.markdown_generator.generate(
                file=command_file,
                body=command.prompt,
                metadata={"description": command.description, "name": name, **command.metadata},
                allowed_metadata=self.__ALLOWED_COMMAND_METADATA,
            )

            self.tracker.track(f"Created {command_file}")

    def rules(self, rules: list[Rule], mode: RuleMode) -> None:
        if not rules:
            return

        if mode == RuleMode.MERGED:
            rules_file = Path(self.agent.rules_file)
            rules_file.parent.mkdir(parents=True, exist_ok=True)
            body = f"# {self.project.name} guidelines"

            for rule in rules:
                body += f"\n\n## {rule.description}"
                body += f"\n\n{rule.prompt}"

            self.markdown_generator.generate(file=rules_file, body=body)

            self.tracker.track(f"Created {rules_file}")
            return

        rules_dir = Path(self.project.dir) / self.agent.rules_dir
        rules_dir.mkdir(parents=True, exist_ok=True)
        for rule in rules:
            filename = f"{rule.name}.{self.agent.rules_extension}"
            if self.project.namespace is not None:
                filename = f"{self.project.namespace}.{filename}"

            command_file = rules_dir / filename
            self.markdown_generator.generate(
                file=command_file,
                body=rule.prompt,
                metadata={"description": rule.description, **rule.metadata},
                allowed_metadata=self.__ALLOWED_INSTRUCTION_METADATA,
            )

            self.tracker.track(f"Created {command_file}")

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        file = Path(self.project.dir) / Path(self.agent.mcp_file)
        self.mcp_server_generator.generate(file, mcp_servers)

    def assets(self, assets: list[str]) -> None:
        for asset in assets:
            asset_path = Path(asset)
            charlie_assets = Path(self.project.dir) / ".charlie" / "assets"
            relative_path = asset_path.relative_to(charlie_assets)
            destination = Path(self.agent.dir) / "assets" / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, destination)
            self.tracker.track(f"Created {asset}")
