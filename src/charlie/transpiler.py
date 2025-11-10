from pathlib import Path

from charlie.agents.registry import AgentSpecRegistry
from charlie.config_reader import parse_config
from charlie.configurator import AgentConfigurator
from charlie.schema import ProjectConfig


class CommandTranspiler:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = parse_config(config_path)
        resolved_config_path = Path(config_path).resolve()
        if resolved_config_path.is_dir():
            if resolved_config_path.name == ".charlie":
                self.root_dir = str(resolved_config_path.parent)
            else:
                self.root_dir = str(resolved_config_path)
        else:
            self.root_dir = str(resolved_config_path.parent)

    def generate(
        self,
        agent_name: str,
        commands: bool = True,
        mcp: bool = False,
        rules: bool = False,
        rules_mode: str = "merged",
        output_dir: str = ".",
    ) -> dict[str, list[str]]:
        registry = AgentSpecRegistry()
        agent_spec = registry.get(agent_name)

        if self.config.project is None:
            self.config.project = ProjectConfig(name="unknown", command_prefix=None)

        configurator = AgentConfigurator.create(
            agent_spec=agent_spec,
            project_config=self.config.project,
            root_dir=self.root_dir,
        )

        generation_results: dict[str, list[str]] = {}

        if commands:
            generated_commands = configurator.commands(self.config.commands, output_dir)
            generation_results["commands"] = generated_commands

        if mcp and self.config.mcp_servers:
            mcp_file = configurator.mcp_servers(self.config, output_dir)
            generation_results["mcp"] = [mcp_file]

        if rules:
            rules_files = configurator.rules(self.config, output_dir, rules_mode)
            generation_results["rules"] = rules_files

        return generation_results

    def generate_mcp(self, agent_name: str, output_dir: str = ".") -> str:
        registry = AgentSpecRegistry()
        agent_spec = registry.get(agent_name)

        if self.config.project is None:
            self.config.project = ProjectConfig(name="unknown", command_prefix=None)

        configurator = AgentConfigurator.create(
            agent_spec=agent_spec,
            project_config=self.config.project,
            root_dir=self.root_dir,
        )

        return configurator.mcp_servers(self.config, output_dir)

    def generate_rules(
        self,
        agent_name: str,
        output_dir: str = ".",
        mode: str = "merged",
    ) -> list[str]:
        registry = AgentSpecRegistry()
        agent_spec = registry.get(agent_name)

        if self.config.project is None:
            self.config.project = ProjectConfig(name="unknown", command_prefix=None)

        configurator = AgentConfigurator.create(
            agent_spec=agent_spec,
            project_config=self.config.project,
            root_dir=self.root_dir,
        )

        return configurator.rules(self.config, output_dir, mode)
