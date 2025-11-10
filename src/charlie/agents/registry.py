from charlie.schema import AgentSpec


class AgentSpecRegistry:
    _AGENT_SPECS: dict[str, dict[str, str]] = {
        "claude": {
            "name": "Claude Code",
            "command_dir": ".claude/commands",
            "rules_file": "CLAUDE.md",
            "rules_dir": ".claude/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": ".claude/mcp.json",
        },
        "copilot": {
            "name": "GitHub Copilot",
            "command_dir": ".github/prompts",
            "rules_file": ".github/copilot-instructions.md",
            "rules_dir": ".github",
            "file_format": "markdown",
            "command_extension": ".prompt.md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "cursor": {
            "name": "Cursor",
            "command_dir": ".cursor/commands",
            "rules_file": ".cursorrules",
            "rules_dir": ".cursor/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".mdc",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": ".cursor/mcp.json",
        },
        "gemini": {
            "name": "Gemini CLI",
            "command_dir": ".gemini/commands",
            "rules_file": "GEMINI.md",
            "rules_dir": ".gemini/rules",
            "file_format": "toml",
            "command_extension": ".toml",
            "rules_extension": ".md",
            "arg_placeholder": "{{args}}",
            "mcp_config_path": "mcp-config.json",
        },
        "qwen": {
            "name": "Qwen Code",
            "command_dir": ".qwen/commands",
            "rules_file": "QWEN.md",
            "rules_dir": ".qwen/rules",
            "file_format": "toml",
            "command_extension": ".toml",
            "rules_extension": ".md",
            "arg_placeholder": "{{args}}",
            "mcp_config_path": "mcp-config.json",
        },
        "windsurf": {
            "name": "Windsurf",
            "command_dir": ".windsurf/workflows",
            "rules_file": ".windsurf/rules/charlie-rules.md",
            "rules_dir": ".windsurf/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "kilocode": {
            "name": "Kilo Code",
            "command_dir": ".kilocode/workflows",
            "rules_file": ".kilocode/rules/charlie-rules.md",
            "rules_dir": ".kilocode/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "opencode": {
            "name": "opencode",
            "command_dir": ".opencode/command",
            "rules_file": "OPENCODE.md",
            "rules_dir": ".opencode/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "codex": {
            "name": "Codex CLI",
            "command_dir": ".codex/prompts",
            "rules_file": "CODEX.md",
            "rules_dir": ".codex/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "auggie": {
            "name": "Auggie CLI",
            "command_dir": ".augment/commands",
            "rules_file": ".augment/rules/charlie-rules.md",
            "rules_dir": ".augment/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "roo": {
            "name": "Roo Code",
            "command_dir": ".roo/commands",
            "rules_file": ".roo/rules/charlie-rules.md",
            "rules_dir": ".roo/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "codebuddy": {
            "name": "CodeBuddy CLI",
            "command_dir": ".codebuddy/commands",
            "rules_file": "CODEBUDDY.md",
            "rules_dir": ".codebuddy/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "amp": {
            "name": "Amp",
            "command_dir": ".agents/commands",
            "rules_file": "AGENTS.md",
            "rules_dir": ".agents/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
        "q": {
            "name": "Amazon Q Developer CLI",
            "command_dir": ".amazonq/prompts",
            "rules_file": "AMAZONQ.md",
            "rules_dir": ".amazonq/rules",
            "file_format": "markdown",
            "command_extension": ".md",
            "rules_extension": ".md",
            "arg_placeholder": "$ARGUMENTS",
            "mcp_config_path": "mcp-config.json",
        },
    }

    def get(self, agent_name: str) -> AgentSpec:
        if agent_name not in self._AGENT_SPECS:
            raise ValueError(f"Unknown agent: {agent_name}. Supported agents: {', '.join(self.list())}")

        agent_spec = self._AGENT_SPECS[agent_name]

        return AgentSpec(
            name=agent_spec["name"],
            command_dir=agent_spec["command_dir"],
            rules_file=agent_spec["rules_file"],
            rules_dir=agent_spec["rules_dir"],
            file_format=agent_spec["file_format"],
            command_extension=agent_spec["command_extension"],
            rules_extension=agent_spec["rules_extension"],
            arg_placeholder=agent_spec["arg_placeholder"],
            mcp_config_path=agent_spec["mcp_config_path"],
        )

    def list(self) -> list[str]:
        return sorted(self._AGENT_SPECS.keys())


def get_agent_spec(agent_name: str) -> AgentSpec:
    registry = AgentSpecRegistry()
    return registry.get(agent_name)


def list_supported_agents() -> list[str]:
    registry = AgentSpecRegistry()
    return registry.list()
