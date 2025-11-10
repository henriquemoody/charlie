import shutil
from pathlib import Path

from charlie.agents.base import BaseAgentAdapter
from charlie.agents.claude import ClaudeAdapter
from charlie.agents.copilot import CopilotAdapter
from charlie.agents.cursor import CursorAdapter
from charlie.agents.gemini import GeminiAdapter
from charlie.agents.qwen import QwenAdapter
from charlie.enums import FileFormat
from charlie.mcp import generate_mcp_config
from charlie.rules import generate_rules_for_agents
from charlie.schema import AgentSpec, CharlieConfig, Command, ProjectConfig

AGENT_ADAPTER_CLASSES: dict[str, type[BaseAgentAdapter]] = {
    "claude": ClaudeAdapter,
    "copilot": CopilotAdapter,
    "cursor": CursorAdapter,
    "gemini": GeminiAdapter,
    "qwen": QwenAdapter,
}


class AgentConfigurator:
    def __init__(
        self,
        agent_spec: AgentSpec,
        project_config: ProjectConfig,
        root_dir: str = ".",
    ):
        self.agent_spec = agent_spec
        self.project_config = project_config
        self.root_dir = root_dir
        self._adapter = self._create_adapter()

    @classmethod
    def create(
        cls,
        agent_spec: AgentSpec,
        project_config: ProjectConfig,
        root_dir: str = ".",
    ) -> "AgentConfigurator":
        return cls(agent_spec, project_config, root_dir)

    def commands(self, commands: list[Command], output_dir: str = ".") -> list[str]:
        command_prefix = self.project_config.command_prefix
        return self._adapter.generate_commands(commands, command_prefix, output_dir)

    def rules(
        self,
        config: CharlieConfig,
        output_dir: str = ".",
        mode: str = "merged",
    ) -> list[str]:
        return generate_rules_for_agents(
            config,
            self.agent_spec.name,
            self.agent_spec,
            output_dir,
            mode=mode,
            root_dir=self.root_dir,
        )

    def mcp_servers(self, config: CharlieConfig, output_dir: str = ".") -> str:
        return generate_mcp_config(
            config,
            self.agent_spec.name,
            output_dir,
            self.agent_spec,
            self.root_dir,
        )

    def assets(self, output_dir: str = ".") -> list[str]:
        source_assets_dir = Path(self.root_dir) / ".charlie" / "assets"

        if not source_assets_dir.exists() or not source_assets_dir.is_dir():
            return []

        agent_base_dir = Path(self.agent_spec.command_dir).parent
        target_assets_dir = Path(output_dir) / agent_base_dir / "assets"

        if target_assets_dir.exists():
            shutil.rmtree(target_assets_dir)

        shutil.copytree(source_assets_dir, target_assets_dir)

        copied_files = []
        for file_path in target_assets_dir.rglob("*"):
            if file_path.is_file():
                copied_files.append(str(file_path))

        return copied_files

    def _create_adapter(self) -> BaseAgentAdapter:
        agent_name = self.agent_spec.name.lower().replace(" ", "")

        for key in AGENT_ADAPTER_CLASSES:
            if key in agent_name or agent_name in key:
                adapter_class = AGENT_ADAPTER_CLASSES[key]
                return adapter_class(self.agent_spec, self.root_dir)

        if self.agent_spec.file_format == FileFormat.MARKDOWN.value:
            return ClaudeAdapter(self.agent_spec, self.root_dir)

        raise ValueError(f"No adapter found for agent: {self.agent_spec.name}")
