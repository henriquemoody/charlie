from charlie.enums import FileFormat
from charlie.schema import Agent


class AgentRegistry:
    _AGENTS: list[Agent] = [
        Agent(
            name="Claude Code",
            shortname="claude",
            dir=".claude",
            default_format=FileFormat.MARKDOWN,
            commands_dir=".claude/commands",
            commands_extension="md",
            commands_shorthand_injection="$ARGUMENTS",
            rules_file="CLAUDE.md",
            rules_dir=".claude/rules",
            rules_extension="md",
            mcp_file=".claude/mcp.json",
            ignore_file=".claude/settings.local.json",
        ),
        Agent(
            name="Cursor",
            shortname="cursor",
            dir=".cursor",
            default_format=FileFormat.MARKDOWN,
            commands_dir=".cursor/commands",
            commands_extension="md",
            commands_shorthand_injection="$ARGUMENTS",
            rules_file=".cursor/rules",
            rules_dir=".cursor/rules",
            rules_extension="mdc",
            mcp_file=".cursor/mcp.json",
            ignore_file=".cursorignore",
        ),
        Agent(
            name="GitHub Copilot",
            shortname="copilot",
            dir=".github",
            default_format=FileFormat.MARKDOWN,
            commands_dir=".github/prompts",
            commands_extension="prompt.md",
            commands_shorthand_injection="$ARGUMENTS",
            rules_file="copilot-instructions.md",
            rules_dir=".github/instructions",
            rules_extension="md",
            mcp_file=".github/copilot/mcp.json",
            ignore_file=".github/.copilotignore",
        ),
    ]

    def get(self, agent_name: str) -> Agent:
        for agent in self._AGENTS:
            if agent.shortname == agent_name:
                return agent

        raise ValueError(f"Unknown agent: {agent_name}. Supported agents: {', '.join(self.list())}")

    def list(self) -> list[str]:
        return sorted([agent.shortname for agent in self._AGENTS])
