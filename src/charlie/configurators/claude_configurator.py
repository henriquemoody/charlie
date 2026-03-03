import json
from pathlib import Path
from typing import Any, final

from charlie.assets_manager import AssetsManager
from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.enums import RuleMode
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Command, MCPServer, Project, Rule, Skill, Subagent
from charlie.tracker import Tracker


@final
class ClaudeConfigurator(AgentConfigurator):
    COMMANDS_DIR = ".claude/commands"
    COMMANDS_EXTENSION = "md"
    COMMANDS_SHORTHAND_INJECTION = "$ARGUMENTS"
    RULES_FILE = "CLAUDE.md"
    RULES_DIR = ".claude/rules"
    RULES_EXTENSION = "md"
    SUBAGENTS_DIR = ".claude/agents"
    SUBAGENTS_EXTENSION = "md"
    SKILLS_DIR = ".claude/skills"
    SKILLS_FILE = "SKILL.md"
    MCP_FILE = ".mcp.json"
    SETTINGS_FILE = ".claude/settings.local.json"
    ASSETS_DIR = ".claude/assets"

    __ALLOWED_COMMAND_METADATA = ["description", "allowed-tools", "argument-hint", "model", "disable-model-invocation"]
    __ALLOWED_INSTRUCTION_METADATA = ["description"]
    __ALLOWED_SUBAGENT_METADATA = [
        "tools",
        "disallowedTools",
        "model",
        "permissionMode",
        "maxTurns",
        "skills",
        "mcpServers",
        "hooks",
        "memory",
        "background",
        "isolation",
    ]
    __ALLOWED_SKILL_METADATA = [
        "description",
        "argument-hint",
        "disable-model-invocation",
        "user-invocable",
        "allowed-tools",
        "model",
        "context",
        "agent",
    ]

    def __init__(
        self,
        project: Project,
        tracker: Tracker,
        markdown_generator: MarkdownGenerator,
        mcp_server_generator: MCPServerGenerator,
        assets_manager: AssetsManager,
        short_name: str,
    ):
        self.project = project
        self.tracker = tracker
        self.markdown_generator = markdown_generator
        self.mcp_server_generator = mcp_server_generator
        self.assets_manager = assets_manager
        self.short_name = short_name

    def placeholders(self) -> dict[str, str]:
        return {
            "agent_name": "Claude Code",
            "agent_shortname": self.short_name,
            "agent_dir": ".claude",
            "commands_dir": self.COMMANDS_DIR,
            "commands_shorthand_injection": self.COMMANDS_SHORTHAND_INJECTION,
            "rules_dir": self.RULES_DIR,
            "rules_file": self.RULES_FILE,
            "subagents_dir": self.SUBAGENTS_DIR,
            "skills_dir": self.SKILLS_DIR,
            "mcp_file": self.MCP_FILE,
            "assets_dir": self.ASSETS_DIR,
        }

    def commands(self, commands: list[Command]) -> None:
        commands_dir = Path(self.project.dir) / self.COMMANDS_DIR
        commands_dir.mkdir(parents=True, exist_ok=True)
        for command in commands:
            name = command.name
            filename = f"{name}.{self.COMMANDS_EXTENSION}"
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

        rules_file = Path(self.project.dir) / self.RULES_FILE
        rules_file.parent.mkdir(parents=True, exist_ok=True)

        if mode == RuleMode.MERGED:
            body = f"# {self.project.name}\n\n"

            for rule in rules:
                body += f"## {rule.description}\n\n"
                body += f"{rule.prompt}\n\n"

            self.markdown_generator.generate(file=rules_file, body=body.rstrip())
            self.tracker.track(f"Created {rules_file}")
            return

        rules_dir = Path(self.project.dir) / self.RULES_DIR
        rules_dir.mkdir(parents=True, exist_ok=True)

        body = f"# {self.project.name}\n\n"

        for rule in rules:
            filename = f"{rule.name}.{self.RULES_EXTENSION}"
            if self.project.namespace is not None:
                filename = f"{self.project.namespace}-{filename}"

            rule_file = rules_dir / filename
            self.markdown_generator.generate(
                file=rule_file,
                body=rule.prompt,
                metadata={"description": rule.description, **rule.metadata},
                allowed_metadata=self.__ALLOWED_INSTRUCTION_METADATA,
            )

            relative_path = f"{self.RULES_DIR}/{filename}"
            body += f"## {rule.description}\n\n"
            body += f"@{relative_path}\n\n"

            self.tracker.track(f"Created {rule_file}")

        self.markdown_generator.generate(file=rules_file, body=body.rstrip())
        self.tracker.track(f"Created {rules_file}")

    def subagents(self, subagents: list[Subagent]) -> None:
        if not subagents:
            return

        subagents_dir = Path(self.project.dir) / self.SUBAGENTS_DIR
        subagents_dir.mkdir(parents=True, exist_ok=True)

        for subagent in subagents:
            name = subagent.name
            filename = f"{name}.{self.SUBAGENTS_EXTENSION}"
            if self.project.namespace is not None:
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
        if not skills:
            return

        skills_dir = Path(self.project.dir) / self.SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)

        for skill in skills:
            name = skill.name
            if self.project.namespace is not None:
                name = f"{self.project.namespace}-{name}"

            skill_dir = skills_dir / name
            skill_dir.mkdir(parents=True, exist_ok=True)

            skill_file = skill_dir / self.SKILLS_FILE
            self.markdown_generator.generate(
                file=skill_file,
                body=skill.prompt,
                metadata={**skill.metadata, "name": name, "description": skill.description},
                allowed_metadata=["name", *self.__ALLOWED_SKILL_METADATA],
            )

            self.tracker.track(f"Created {skill_file}")

    def mcp_servers(self, mcp_servers: list[MCPServer]) -> None:
        if not mcp_servers:
            return

        file = Path(self.project.dir) / self.MCP_FILE
        self.mcp_server_generator.generate(file, mcp_servers)

        settings_file_path = Path(self.project.dir) / self.SETTINGS_FILE
        settings_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing settings if file exists
        existing_settings: dict[str, Any] = {}
        if settings_file_path.exists():
            try:
                with open(settings_file_path, encoding="utf-8") as f:
                    existing_settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing_settings = {}

        # Get server names
        server_names = [server.name for server in mcp_servers]

        # Update or create enabledMcpjsonServers
        if "enabledMcpjsonServers" not in existing_settings:
            existing_settings["enabledMcpjsonServers"] = []

        # Merge server names, avoiding duplicates
        existing_servers = existing_settings["enabledMcpjsonServers"]
        for server_name in server_names:
            if server_name not in existing_servers:
                existing_servers.append(server_name)

        existing_settings["enabledMcpjsonServers"] = existing_servers

        # Write updated settings
        with open(settings_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_settings, f, indent=2)
            f.write("\n")

        self.tracker.track(f"Enabled MCP servers in {settings_file_path}")

    def assets(self, assets: list[str]) -> None:
        if not assets:
            return

        destination_base = Path(self.ASSETS_DIR)
        self.assets_manager.copy_assets(assets, destination_base)

    def ignore_file(self, patterns: list[str]) -> None:
        if not patterns:
            self.tracker.track("No ignore patterns to add for Claude Code")
            return

        settings_file_path = Path(self.project.dir) / self.SETTINGS_FILE
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
        deny_rules = [f"Read(./{pattern})" for pattern in patterns]

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
