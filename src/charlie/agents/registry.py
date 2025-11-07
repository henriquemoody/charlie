from charlie.schema import AgentSpec

AGENT_SPECS: dict[str, dict[str, str]] = {
    "claude": {
        "name": "Claude Code",
        "command_dir": ".claude/commands",
        "rules_file": "CLAUDE.md",
        "rules_dir": ".claude/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "command_dir": ".github/prompts",
        "rules_file": ".github/copilot-instructions.md",
        "rules_dir": ".github",
        "file_format": "markdown",
        "file_extension": ".prompt.md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "cursor": {
        "name": "Cursor",
        "command_dir": ".cursor/commands",
        "rules_file": "CURSOR.md",
        "rules_dir": ".cursor/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "gemini": {
        "name": "Gemini CLI",
        "command_dir": ".gemini/commands",
        "rules_file": "GEMINI.md",
        "rules_dir": ".gemini/rules",
        "file_format": "toml",
        "file_extension": ".toml",
        "arg_placeholder": "{{args}}",
    },
    "qwen": {
        "name": "Qwen Code",
        "command_dir": ".qwen/commands",
        "rules_file": "QWEN.md",
        "rules_dir": ".qwen/rules",
        "file_format": "toml",
        "file_extension": ".toml",
        "arg_placeholder": "{{args}}",
    },
    "windsurf": {
        "name": "Windsurf",
        "command_dir": ".windsurf/workflows",
        "rules_file": ".windsurf/rules/charlie-rules.md",
        "rules_dir": ".windsurf/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "kilocode": {
        "name": "Kilo Code",
        "command_dir": ".kilocode/workflows",
        "rules_file": ".kilocode/rules/charlie-rules.md",
        "rules_dir": ".kilocode/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "opencode": {
        "name": "opencode",
        "command_dir": ".opencode/command",
        "rules_file": "OPENCODE.md",
        "rules_dir": ".opencode/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "codex": {
        "name": "Codex CLI",
        "command_dir": ".codex/prompts",
        "rules_file": "CODEX.md",
        "rules_dir": ".codex/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "auggie": {
        "name": "Auggie CLI",
        "command_dir": ".augment/commands",
        "rules_file": ".augment/rules/charlie-rules.md",
        "rules_dir": ".augment/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "roo": {
        "name": "Roo Code",
        "command_dir": ".roo/commands",
        "rules_file": ".roo/rules/charlie-rules.md",
        "rules_dir": ".roo/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "codebuddy": {
        "name": "CodeBuddy CLI",
        "command_dir": ".codebuddy/commands",
        "rules_file": "CODEBUDDY.md",
        "rules_dir": ".codebuddy/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "amp": {
        "name": "Amp",
        "command_dir": ".agents/commands",
        "rules_file": "AGENTS.md",
        "rules_dir": ".agents/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "command_dir": ".amazonq/prompts",
        "rules_file": "AMAZONQ.md",
        "rules_dir": ".amazonq/rules",
        "file_format": "markdown",
        "file_extension": ".md",
        "arg_placeholder": "$ARGUMENTS",
    },
}


def get_agent_spec(agent_name: str) -> AgentSpec:
    if agent_name not in AGENT_SPECS:
        raise ValueError(f"Unknown agent: {agent_name}. Supported agents: {', '.join(list_supported_agents())}")

    agent_spec = AGENT_SPECS[agent_name]

    return AgentSpec(
        name=agent_spec["name"],
        command_dir=agent_spec["command_dir"],
        rules_file=agent_spec["rules_file"],
        rules_dir=agent_spec["rules_dir"],
        file_format=agent_spec["file_format"],
        file_extension=agent_spec["file_extension"],
        arg_placeholder=agent_spec["arg_placeholder"],
    )


def list_supported_agents() -> list[str]:
    return sorted(AGENT_SPECS.keys())
