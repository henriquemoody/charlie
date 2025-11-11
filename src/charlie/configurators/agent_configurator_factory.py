from charlie.configurators.agent_configurator import AgentConfigurator
from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.configurators.copilot_configurator import CopilotConfigurator
from charlie.configurators.cursor_configurator import CursorConfigurator
from charlie.markdown_generator import MarkdownGenerator
from charlie.schema import Agent, Project
from charlie.tracker import Tracker


class AgentConfiguratorFactory:
    @staticmethod
    def create(agent: Agent, project: Project, tracker: Tracker) -> AgentConfigurator:
        if agent.shortname == "cursor":
            return CursorConfigurator(agent, project, tracker, MarkdownGenerator())

        if agent.shortname == "claude":
            return ClaudeConfigurator(agent, project, tracker, MarkdownGenerator())

        if agent.shortname == "copilot":
            return CopilotConfigurator(agent, project, tracker, MarkdownGenerator())

        raise ValueError(f"Unsupported agent: {agent.shortname}")
