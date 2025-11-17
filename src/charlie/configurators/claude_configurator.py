import json
from pathlib import Path
from typing import Any, final

from charlie.assets_manager import AssetsManager
from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Agent, Command, MCPServer, Project, Rule
from charlie.tracker import Tracker


@final
class ClaudeConfigurator(AgentConfigurator):
    __ALLOWED_COMMAND_METADATA = ["description", "allowed-tools", "argument-hint", "model", "disable-model-invocation"]
    __ALLOWED_INSTRUCTION_METADATA = ["description"]

    def __init__(
        self,
        agent: Agent,
        project: Project,
        tracker: Tracker,
        markdown_generator: MarkdownGenerator,
        mcp_server_generator: MCPServerGenerator,
        assets_manager: AssetsManager,
    ):
        self.agent = agent
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator
        self.mcp_server_generator = mcp_server_generator
        self.assets_manager = assets_manager

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
        file = Path(self.project.dir) / Path(self.agent.mcp_file)
        self.mcp_server_generator.generate(file, mcp_servers)

    def assets(self, assets: list[str]) -> None:
        if not assets:
            return

        source_base = Path(self.project.dir) / ".charlie" / "assets"
        destination_base = Path(self.agent.dir) / "assets"
        self.assets_manager.copy_assets(assets, source_base, destination_base)

    def ignore_file(self, patterns: list[str]) -> None:
        if self.agent.ignore_file is None:
            return

        if not patterns:
            self.tracker.track("No ignore patterns to add for Claude Code")
            return

        settings_file_path = Path(self.project.dir) / self.agent.ignore_file
        self.tracker.track(f"Configuring Claude Code ignore patterns in {settings_file_path}")

        # Read existing settings if file exists
        existing_settings: dict[str, Any] = {}
        if settings_file_path.exists():
            try:
                with open(settings_file_path, encoding="utf-8") as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                # If file is corrupted or can't be read, start fresh
                existing_settings = {}

        # Convert patterns to Claude's permission deny format
        deny_rules = [f"Read({pattern})" for pattern in patterns]

        # Merge with existing permissions
        if "permissions" not in existing_settings:
            existing_settings["permissions"] = {}

        if "deny" not in existing_settings["permissions"]:
            existing_settings["permissions"]["deny"] = []

        # Get existing deny rules
        existing_deny = existing_settings["permissions"]["deny"]

        # Add new rules, avoiding duplicates
        for rule in deny_rules:
            if rule not in existing_deny:
                existing_deny.append(rule)

        existing_settings["permissions"]["deny"] = existing_deny

        # Ensure parent directory exists
        settings_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write updated settings
        with open(settings_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_settings, f, indent=2)
            f.write("\n")  # Add trailing newline

        self.tracker.track(f"Updated ignore patterns in {settings_file_path}")
