"""Core transpiler engine for command generation."""

from pathlib import Path

from charlie.agents import get_agent_spec
from charlie.agents.base import BaseAgentAdapter
from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.agents.registry import AgentSpec
from charlie.mcp import generate_mcp_config
from charlie.parser import parse_config
from charlie.rules import generate_rules_for_agents

ADAPTER_CLASSES: dict[str, type[BaseAgentAdapter]] = {
    "claude": ClaudeAdapter,
    "copilot": CopilotAdapter,
    "cursor": CursorAdapter,
    "gemini": GeminiAdapter,
    "qwen": QwenAdapter,
}


class CommandTranspiler:
    """Main transpiler engine for generating agent-specific configurations."""

    def __init__(self, config_path: str):
        """Initialize transpiler with configuration file.

        Args:
            config_path: Path to charlie YAML configuration file or directory

        Raises:
            FileNotFoundError: If config file doesn't exist
            ConfigParseError: If config is invalid
        """
        self.config_path = config_path
        self.config = parse_config(config_path)
        config_path_obj = Path(config_path).resolve()
        if config_path_obj.is_dir():
            if config_path_obj.name == ".charlie":
                self.root_dir = str(config_path_obj.parent)
            else:
                self.root_dir = str(config_path_obj)
        else:
            self.root_dir = str(config_path_obj.parent)

    def generate(
        self,
        agent_name: str,
        mcp: bool = False,
        rules: bool = False,
        rules_mode: str = "merged",
        output_dir: str = ".",
    ) -> dict[str, list[str]]:
        """Generate outputs based on runtime preferences.

        Args:
            agent: Agent name to generate for (None = no agent)
            mcp: Whether to generate MCP server configs
            rules: Whether to generate rules files
            rules_mode: Rules generation mode ("merged" or "separate")
            output_dir: Base output directory

        Returns:
            Dictionary mapping target names to list of generated files:
            - "commands": List of generated command file paths
            - "mcp": List containing the MCP config file path
            - "rules": List of generated rules file paths

        Raises:
            ValueError: If agent is not supported
        """
        results = {}

        agent_spec = get_agent_spec(agent_name)
        adapter = self._get_adapter(agent_name, agent_spec)

        command_prefix = self.config.project.command_prefix if self.config.project else None
        files = adapter.generate_commands(self.config.commands, command_prefix, output_dir)
        results["commands"] = files

        if mcp:
            mcp_file = generate_mcp_config(self.config, agent_name, output_dir)
            results["mcp"] = [mcp_file]

        if rules and agent_name:
            rules_files = generate_rules_for_agents(
                self.config,
                agent_name,
                agent_spec,
                output_dir,
                mode=rules_mode,
                root_dir=self.root_dir,
            )
            results["rules"] = rules_files

        return results

    def generate_mcp(self, agent_name: str, output_dir: str = ".") -> str:
        """Generate only MCP server configs.

        Args:
            output_dir: Output directory
            agent: Agent name for agent-specific paths

        Returns:
            Path to generated MCP config file

        Raises:
            ValueError: If no MCP servers defined in config
        """
        return generate_mcp_config(self.config, agent_name, output_dir)

    def generate_rules(
        self,
        agent_name: str,
        output_dir: str = ".",
        mode: str = "merged",
    ) -> list[str]:
        """Generate only rules files for specified agent.

        Args:
            agent: Agent name
            output_dir: Output directory
            mode: Rules generation mode ("merged" or "separate")

        Returns:
            List of generated rules file paths
        """
        agent_spec = get_agent_spec(agent_name)

        return generate_rules_for_agents(
            self.config, agent_name, agent_spec, output_dir, mode=mode, root_dir=self.root_dir
        )

    def _get_adapter(self, agent_name: str, agent_spec: AgentSpec) -> BaseAgentAdapter:
        """Get adapter instance for an agent.

        Args:
            agent_name: Name of the agent
            agent_spec: Agent specification

        Returns:
            Adapter instance

        Raises:
            ValueError: If agent doesn't have a registered adapter
        """
        if agent_name not in ADAPTER_CLASSES:
            if agent_spec.file_format == "markdown":
                return ClaudeAdapter(agent_spec, self.root_dir)
            else:
                raise ValueError(f"No adapter registered for agent: {agent_name}")

        adapter_class = ADAPTER_CLASSES[agent_name]
        return adapter_class(agent_spec, self.root_dir)
