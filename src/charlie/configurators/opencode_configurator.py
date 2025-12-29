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
class OpencodeConfigurator(AgentConfigurator):
    __ALLOWED_COMMAND_METADATA = ["description"]
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

        if mode == RuleMode.MERGED:
            instructions_file = Path(self.project.dir) / self.agent.rules_file
            instructions_file.parent.mkdir(parents=True, exist_ok=True)

            body = f"# {self.project.name}\n\n"

            for rule in rules:
                body += f"## {rule.description}\n\n"
                body += f"{rule.prompt}\n\n"

            self.markdown_generator.generate(file=instructions_file, body=body.rstrip())
            self.tracker.track(f"Created {instructions_file}")

            # Add instructions to opencode.json
            self._update_opencode_config({"instructions": [str(instructions_file.relative_to(self.project.dir))]})
            return

        rules_dir = Path(self.project.dir) / self.agent.rules_dir
        rules_dir.mkdir(parents=True, exist_ok=True)

        body = f"# {self.project.name}\n\n"
        instruction_paths = []

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
            body += f"See @{relative_path}\n\n"

            instruction_paths.append(relative_path)

            self.tracker.track(f"Created {rule_file}")

        instructions_file = Path(self.project.dir) / self.agent.rules_file
        self.markdown_generator.generate(file=instructions_file, body=body.rstrip())
        self.tracker.track(f"Created {instructions_file}")

        # Add all instruction paths to opencode.json
        all_instructions = [str(instructions_file.relative_to(self.project.dir))] + instruction_paths
        self._update_opencode_config({"instructions": all_instructions})

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        if not mcp_servers:
            return

        file = Path(self.project.dir) / self.agent.mcp_file
        self.mcp_server_generator.generate(file, mcp_servers)

    def assets(self, assets: list[str]) -> None:
        if not assets:
            return

        source_base = Path(self.project.dir) / ".charlie" / "assets"
        destination_base = Path(self.project.dir) / self.agent.dir / "assets"
        self.assets_manager.copy_assets(assets, source_base, destination_base)

    def ignore_file(self, patterns: list[str]) -> None:
        if self.agent.ignore_file is None:
            return

        if not patterns:
            return

        # Add patterns to the "watcher" key in opencode.json
        watcher_config = {"ignore": patterns}
        self._update_opencode_config({"watcher": watcher_config})

        self.tracker.track("Added ignore patterns to opencode.json")

    def _update_opencode_config(self, updates: dict[str, Any]) -> None:
        """Update the opencode.json configuration file with new settings."""
        if self.agent.ignore_file is None:
            return

        config_file_path = Path(self.project.dir) / self.agent.ignore_file

        # Read existing config if file exists
        existing_config: dict[str, Any] = {}
        if config_file_path.exists():
            try:
                with open(config_file_path, encoding="utf-8") as f:
                    existing_config = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing_config = {}

        # Merge updates into existing config
        for key, value in updates.items():
            if key in existing_config and isinstance(existing_config[key], dict) and isinstance(value, dict):
                # Merge dictionaries
                existing_config[key].update(value)
            elif key in existing_config and isinstance(existing_config[key], list) and isinstance(value, list):
                # Merge lists, avoiding duplicates
                existing_list = existing_config[key]
                for item in value:
                    if item not in existing_list:
                        existing_list.append(item)
            else:
                # Replace value
                existing_config[key] = value

        # Write updated config
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2)
            f.write("\n")

