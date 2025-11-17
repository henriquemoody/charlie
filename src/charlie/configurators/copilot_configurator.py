from pathlib import Path
from typing import final

from charlie.assets_manager import AssetsManager
from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Agent, Command, MCPServer, Project, Rule
from charlie.tracker import Tracker


@final
class CopilotConfigurator(AgentConfigurator):
    __ALLOWED_COMMAND_METADATA = ["description"]
    __ALLOWED_INSTRUCTION_METADATA = ["description", "applyTo"]

    def __init__(
        self,
        agent: Agent,
        project: Project,
        tracker: Tracker,
        markdown_generator: MarkdownGenerator,
        assets_manager: AssetsManager,
    ):
        self.agent = agent
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator
        self.assets_manager = assets_manager

    def commands(self, commands: list[Command]) -> None:
        prompts_dir = Path(self.project.dir) / self.agent.commands_dir
        prompts_dir.mkdir(parents=True, exist_ok=True)

        prompts = {}
        # Create individual prompt files
        for command in commands:
            name = command.name
            filename = f"{name}.{self.agent.commands_extension}"
            if self.project.namespace is not None:
                filename = f"{self.project.namespace}-{filename}"

            prompt_file = prompts_dir / filename
            self.markdown_generator.generate(
                file=prompt_file,
                body=command.prompt,
                metadata={"description": command.description, **command.metadata},
                allowed_metadata=self.__ALLOWED_COMMAND_METADATA,
            )

            prompts[name] = (filename, command.description)
            self.tracker.track(f"Created {prompt_file}")

        instructions_file = Path(self.project.dir) / self.agent.rules_dir / "enable-slash-commands.md"
        instructions_file.parent.mkdir(parents=True, exist_ok=True)

        body = f"You can use slash commands from the `{self.agent.commands_dir}` directory. "
        body += "Each command is a reusable prompt that you can invoke with `/command-name`.\n\n"
        body += "Available commands:\n\n"

        for name, (filename, description) in prompts.items():
            body += f"- `/{name}`: {description} (file: `{filename}`)\n"

        self.markdown_generator.generate(
            file=instructions_file, body=body.rstrip(), metadata={"description": "Enable slash commands"}
        )
        self.tracker.track(f"Created {instructions_file}")

    def rules(self, rules: list[Rule], mode: RuleMode) -> None:
        if not rules:
            return

        if mode == RuleMode.MERGED:
            instructions_file = Path(self.project.dir) / self.agent.rules_file
            instructions_file.parent.mkdir(parents=True, exist_ok=True)

            body = f"# {self.project.name}\n\n"

            for rule in rules:
                body += f"## {rule.description}\n\n"
                body += f"{rule.prompt}\n\n"

            self.markdown_generator.generate(file=instructions_file, body=body.rstrip())
            self.tracker.track(f"Created {instructions_file}")
            return

        rules_dir = Path(self.project.dir) / self.agent.rules_dir
        rules_dir.mkdir(parents=True, exist_ok=True)

        body = f"# {self.project.name}\n\n"

        for rule in rules:
            filename = f"{rule.name}-instructions.{self.agent.rules_extension}"
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
            body += f"See @{relative_path}\n\n"

            self.tracker.track(f"Created {rule_file}")

        instructions_file = Path(self.project.dir) / self.agent.rules_file
        self.markdown_generator.generate(file=instructions_file, body=body.rstrip())
        self.tracker.track(f"Created {instructions_file}")

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        if mcp_servers:
            self.tracker.track("GitHub Copilot does not support MCP servers natively. Skipping...")

    def assets(self, assets: list[str]) -> None:
        if not assets:
            return

        source_base = Path(self.project.dir) / ".charlie" / "assets"
        destination_base = Path(self.project.dir) / self.agent.dir / "assets"
        self.assets_manager.copy_assets(assets, source_base, destination_base)

    def ignore_file(self, patterns: list[str]) -> None:
        self.tracker.track("GitHub Copilot does not support ignore files natively. Skipping...")
        pass
