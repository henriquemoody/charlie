"""Agent registry with built-in knowledge of all supported agents."""

# Built-in agent specifications
AGENT_SPECS: dict[str, dict[str, str]] = {
    "claude": {
        "name": "Claude Code",
        "command_dir": ".claude/commands",
        "rules_file": "CLAUDE.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "command_dir": ".github/prompts",
        "rules_file": ".github/copilot-instructions.md",
        "file_format": "markdown",
        "file_extension": ".prompt.md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "cursor": {
        "name": "Cursor",
        "command_dir": ".cursor/commands",
        "rules_file": ".cursor/rules/charlie-rules.mdc",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "gemini": {
        "name": "Gemini CLI",
        "command_dir": ".gemini/commands",
        "rules_file": "GEMINI.md",
        "file_format": "toml",
        "file_extension": ".toml",
        "arg_placeholder": "{{args}}",
    },
    "qwen": {
        "name": "Qwen Code",
        "command_dir": ".qwen/commands",
        "rules_file": "QWEN.md",
        "file_format": "toml",
        "file_extension": ".toml",
        "arg_placeholder": "{{args}}",
    },
    "windsurf": {
        "name": "Windsurf",
        "command_dir": ".windsurf/workflows",
        "rules_file": ".windsurf/rules/charlie-rules.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "kilocode": {
        "name": "Kilo Code",
        "command_dir": ".kilocode/workflows",
        "rules_file": ".kilocode/rules/charlie-rules.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "opencode": {
        "name": "opencode",
        "command_dir": ".opencode/command",
        "rules_file": "OPENCODE.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "codex": {
        "name": "Codex CLI",
        "command_dir": ".codex/prompts",
        "rules_file": "CODEX.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "auggie": {
        "name": "Auggie CLI",
        "command_dir": ".augment/commands",
        "rules_file": ".augment/rules/charlie-rules.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "roo": {
        "name": "Roo Code",
        "command_dir": ".roo/commands",
        "rules_file": ".roo/rules/charlie-rules.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "codebuddy": {
        "name": "CodeBuddy CLI",
        "command_dir": ".codebuddy/commands",
        "rules_file": "CODEBUDDY.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "amp": {
        "name": "Amp",
        "command_dir": ".agents/commands",
        "rules_file": "AGENTS.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "command_dir": ".amazonq/prompts",
        "rules_file": "AMAZONQ.md",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
}


def get_agent_spec(agent_name: str) -> dict[str, str]:
    """Get built-in specification for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent specification dictionary

    Raises:
        ValueError: If agent is not supported
    """
    if agent_name not in AGENT_SPECS:
        raise ValueError(
            f"Unknown agent: {agent_name}. Supported agents: {', '.join(list_supported_agents())}"
        )
    return AGENT_SPECS[agent_name]


def list_supported_agents() -> list[str]:
    """List all supported agent names.

    Returns:
        List of agent names
    """
    return sorted(AGENT_SPECS.keys())


def get_agent_info(agent_name: str) -> dict[str, str] | None:
    """Get detailed information about an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent information dictionary or None if not found
    """
    return AGENT_SPECS.get(agent_name)
