"""Core transpiler engine for command generation."""

from pathlib import Path
from typing import Dict, List, Optional

from charlie.parser import parse_config
from charlie.schema import CharlieConfig
from charlie.agents import get_agent_spec
from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.mcp import generate_mcp_config
from charlie.rules import generate_rules_for_agents


# Map agent names to adapter classes
ADAPTER_CLASSES = {
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
            config_path: Path to charlie YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ConfigParseError: If config is invalid
        """
        self.config_path = config_path
        self.config = parse_config(config_path)

    def generate(
        self,
        agents: Optional[List[str]] = None,
        mcp: bool = False,
        rules: bool = False,
        rules_mode: str = "merged",
        output_dir: str = ".",
    ) -> Dict[str, List[str]]:
        """Generate outputs based on runtime preferences.

        Args:
            agents: List of agent names to generate for (None = no agents)
            mcp: Whether to generate MCP server configs
            rules: Whether to generate rules files
            rules_mode: Rules generation mode ("merged" or "separate")
            output_dir: Base output directory

        Returns:
            Dictionary mapping target names to list of generated files

        Raises:
            ValueError: If agent is not supported
        """
        results = {}

        # Generate agent commands
        if agents:
            for agent_name in agents:
                # Get agent spec and adapter
                spec = get_agent_spec(agent_name)
                adapter = self._get_adapter(agent_name, spec)

                # Generate command files
                files = adapter.generate_commands(
                    self.config.commands, self.config.project.command_prefix, output_dir
                )
                results[f"{agent_name}_commands"] = files

        # Generate MCP configs if requested
        if mcp:
            mcp_file = generate_mcp_config(self.config, output_dir)
            results["mcp"] = [mcp_file]

        # Generate rules if requested
        if rules and agents:
            # Get specs for all agents
            agent_specs = {name: get_agent_spec(name) for name in agents}
            rules_files = generate_rules_for_agents(
                self.config, agents, agent_specs, output_dir, mode=rules_mode
            )
            for agent_name, rules_paths in rules_files.items():
                results[f"{agent_name}_rules"] = rules_paths

        return results

    def generate_mcp(self, output_dir: str = ".") -> str:
        """Generate only MCP server configs.

        Args:
            output_dir: Output directory

        Returns:
            Path to generated MCP config file

        Raises:
            ValueError: If no MCP servers defined in config
        """
        return generate_mcp_config(self.config, output_dir)

    def generate_rules(
        self, agents: List[str], output_dir: str = ".", mode: str = "merged"
    ) -> Dict[str, List[str]]:
        """Generate only rules files for specified agents.

        Args:
            agents: List of agent names
            output_dir: Output directory
            mode: Rules generation mode ("merged" or "separate")

        Returns:
            Dictionary mapping agent names to list of rules file paths
        """
        agent_specs = {name: get_agent_spec(name) for name in agents}
        return generate_rules_for_agents(
            self.config, agents, agent_specs, output_dir, mode=mode
        )

    def _get_adapter(self, agent_name: str, agent_spec: dict):
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
            # For agents without specific adapters yet, use a generic one based on format
            if agent_spec["file_format"] == "markdown":
                return ClaudeAdapter(agent_spec)  # Reuse Claude adapter for markdown
            else:
                raise ValueError(f"No adapter registered for agent: {agent_name}")

        adapter_class = ADAPTER_CLASSES[agent_name]
        return adapter_class(agent_spec)

