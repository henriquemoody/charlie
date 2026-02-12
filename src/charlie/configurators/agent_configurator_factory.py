from charlie.assets_manager import AssetsManager
from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.configurators.copilot_configurator import CopilotConfigurator
from charlie.configurators.cursor_configurator import CursorConfigurator
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.schema import Project
from charlie.tracker import Tracker


class AgentConfiguratorFactory:
    @staticmethod
    def create(agent_name: str, project: Project, tracker: Tracker) -> AgentConfigurator:
        markdown_generator = MarkdownGenerator()
        mcp_server_generator = MCPServerGenerator(tracker)
        assets_manager = AssetsManager(tracker)

        if agent_name == "cursor":
            return CursorConfigurator(
                project, tracker, markdown_generator, mcp_server_generator, assets_manager, agent_name
            )

        if agent_name == "claude":
            return ClaudeConfigurator(
                project, tracker, markdown_generator, mcp_server_generator, assets_manager, agent_name
            )

        if agent_name == "copilot":
            return CopilotConfigurator(project, tracker, markdown_generator, assets_manager, agent_name)

        raise ValueError(f"Unsupported agent: {agent_name}")
