from pathlib import Path

from charlie.agents import get_agent_spec
from charlie.agents.base import BaseAgentAdapter
from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.agents.registry import AgentSpec
from charlie.enums import FileFormat
from charlie.mcp import generate_mcp_config
from charlie.parser import parse_config
from charlie.rules import generate_rules_for_agents

AGENT_ADAPTER_CLASSES: dict[str, type[BaseAgentAdapter]] = {
    "claude": ClaudeAdapter,
    "copilot": CopilotAdapter,
    "cursor": CursorAdapter,
    "gemini": GeminiAdapter,
    "qwen": QwenAdapter,
}


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
        mcp: bool = False,
        rules: bool = False,
        rules_mode: str = "merged",
        output_dir: str = ".",
    ) -> dict[str, list[str]]:
        generation_results = {}

        agent_specification = get_agent_spec(agent_name)
        agent_adapter = self._get_adapter(agent_name, agent_specification)

        command_prefix = self.config.project.command_prefix if self.config.project else None
        generated_command_files = agent_adapter.generate_commands(self.config.commands, command_prefix, output_dir)
        generation_results["commands"] = generated_command_files

        if mcp:
            mcp_config_file = generate_mcp_config(self.config, agent_name, output_dir)
            generation_results["mcp"] = [mcp_config_file]

        if rules and agent_name:
            generated_rules_files = generate_rules_for_agents(
                self.config,
                agent_name,
                agent_specification,
                output_dir,
                mode=rules_mode,
                root_dir=self.root_dir,
            )
            generation_results["rules"] = generated_rules_files

        return generation_results

    def generate_mcp(self, agent_name: str, output_dir: str = ".") -> str:
        return generate_mcp_config(self.config, agent_name, output_dir)

    def generate_rules(
        self,
        agent_name: str,
        output_dir: str = ".",
        mode: str = "merged",
    ) -> list[str]:
        agent_specification = get_agent_spec(agent_name)

        return generate_rules_for_agents(
            self.config, agent_name, agent_specification, output_dir, mode=mode, root_dir=self.root_dir
        )

    def _get_adapter(self, agent_name: str, agent_spec: AgentSpec) -> BaseAgentAdapter:
        if agent_name not in AGENT_ADAPTER_CLASSES:
            if agent_spec.file_format == FileFormat.MARKDOWN.value:
                return ClaudeAdapter(agent_spec, self.root_dir)
            else:
                raise ValueError(f"No adapter registered for agent: {agent_name}")

        adapter_class = AGENT_ADAPTER_CLASSES[agent_name]
        return adapter_class(agent_spec, self.root_dir)
