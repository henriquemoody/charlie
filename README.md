# Charlie - Universal Agent Config Generator

**Define once in YAML/Markdown. Generate agent-specific commands, MCP config, and rules.**

Charlie is a universal agent configuration generator that produces agent-specific commands, MCP configurations, and rules from a single YAML/Markdown spec.

[![Tests](https://img.shields.io/badge/tests-94%20passed-green)]()
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

## Features

- ✨ **Single Definition**: Write settings once in YAML or Markdown
- 🤖 **Multi-Agent Support**: Generate for 15+ AI agents (Claude, Copilot, Cursor, Gemini, Windsurf, and more)
- ⚙️ **Slash Commands Integration**: Generate slash commands from a single definition.
- 🔌 **MCP Integration**: Generate MCP server configurations with tool schemas
- 📋 **Rules Generation**: Create agent-specific rules files with manual preservation
- 🎯 **Auto-Detection**: Automatically finds `charlie.yaml` or `.charlie/` directory
- ⚡ **Runtime Targeting**: Choose which agents to generate for at runtime
- 📦 **Library & CLI**: Use as CLI tool or import as Python library

## Quick Start

### Installation

```bash
pip install charlie-agents
```

## Configuration

For advanced features, Charlie supports two configuration approaches:

1. **Monolithic** - Single YAML file (good for small projects)
2. **Directory-Based** - Modular files in `.charlie/` directories (good for large projects)

### Monolithic Configuration

For advanced features, create `charlie.yaml` in your project:

```yaml
version: "1.0" # Optional: Schema version (defaults to "1.0")

project:
  name: "My project"      # Optional: Inferred from directory name if omitted
  namespace: "my"         # Optional: Used to prefix commands, rules, and MCP servers.

variables:
  mcp_api_token:
    env: MCP_API_TOKEN    # It will ask the user to provide an API token, if the environment variable is not set

# Command definitions
commands:
  - name: "commit"
    description: "Analyze changes and create a high-quality git commit"
    prompt: "Check what changed, and commit your changes. The body of the message explains WHY it changed"

  - name: "command-handler"
    description: "Creates a command handler"
    prompt: "Create a command handler using src/examples/handler.py as an reference"

# MCP server definitions
mcp_servers:
  - name: "local_server"
    transport: "stdio"
    command: "node"
    args: ["server.js"]
    env:
      KEY: "value"

  - name: "remote_server"
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer {{var:mcp_api_token}}"
      Content-Type: "application/json"

# Rules configuration
rules:
  - title: "Commit message standards"
    prompt: "Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)"

  - title: "Coding standards"
    prompt: "All code should follow PEP 8"
```

Charlie will also read `charlie.dist.yaml`, unless you have a `charlie.yaml` in the directory. And both `*.yaml` and `*.yml` extensions are supported.

See [`examples/`](examples/) directory for complete examples:

- [`examples/simple.yaml`](examples/simple.yaml) - Basic configuration
- [`examples/speckit.yaml`](examples/speckit.yaml) - Spec-kit inspired configuration

### Directory-Based Configuration

For better organization and collaboration, use the directory-based approach. The `charlie.yaml` file is **optional** - if you only have a `.charlie/` directory, Charlie will infer the project name from the directory:

```
project/
├── charlie.yaml                  # Optional: Project metadata (name inferred if omitted)
└── .charlie/
    ├── commands/
    │   ├── init.yaml             # One file per command (Markdown or YAML supported)
    │   └── deploy.md
    ├── rules/
    │   ├── commit-messages.yaml  # One file per rule section (Markdown or YAML supported)
    │   └── code-style.md
    └── mcp-servers/
        └── local-tools.yaml      # MCP servers in YAML
```

See [`examples/directory-based/`](examples/directory-based/) for a complete example.

**Benefits:**

- Clear organization (one file per command/rule)
- No merge conflicts on single file
- Easy to add/remove components
- Better for version control diffs
- Native markdown support for rich documentation

### Generate Agent-specific Configuration

```bash
# Generate configuration files for a specific agent (generates commands, MCP, and rules by default)
charlie generate claude
```

### Placeholders

Charlie supports these universal placeholders in commands, rules, and MCP configurations:

**Content Placeholders:**

- `{{user_input}}` → Replaced with agent-specific input placeholder (`$ARGUMENTS` or `{{args}}`)
- `{{agent_name}}` → Replaced with the agent's name (e.g., `Cursor`, `Claude Code`, `GitHub Copilot`)
- `{{project_name}}` → Replaced with the agent's name (e.g., `Cursor`, `Claude Code`, `GitHub Copilot`)

**Path Placeholders:**

- `{{project_dir}}` → Resolves to the project root directory
- `{{agent_dir}}` → Resolves to agent's base directory (e.g., `.claude`, `.cursor`)
- `{{commands_dir}}` → Resolves to agent's commands directory (e.g., `.claude/commands/`)
- `{{rules_dir}}` → Resolves to agent's rules directory (e.g., `.claude/rules/`)
- `{{assets_dir}}` → Resolves to the path of generic assets (copied from `.charlie/assets/`).

**Environment Variable Placeholders:**

- `{{env:VAR_NAME}}` → Replaced with the value of the environment variable
  - Loads from system environment or `.env` file in root directory
  - Raises `EnvironmentVariableNotFoundError` if variable doesn't exist
  - System environment variables take precedence over `.env` file

These placeholders work in commands, rules content, and MCP server configurations (command and args fields).

## Usage

### CLI Commands

#### `charlie generate <agent>`

Setup agent-specific configurations (generates commands, MCP config, and rules by default):

```bash
# Auto-detect charlie.yaml (generates all artifacts)
charlie generate claude

# Setup without MCP config
charlie generate cursor --no-mcp

# Setup without rules
charlie generate claude --no-rules

# Setup without commands
charlie generate claude --no-commandsrules

# Explicit config file
charlie generate gemini --config my-config.yaml

# Custom output directory
charlie generate cursor --output ./build
```

#### `charlie validate`

Validate YAML configuration:

```bash
# Auto-detect charlie.yaml
charlie validate

# Specific file
charlie validate my-config.yaml
```

#### `charlie list-agents`

List all supported AI agents:

```bash
charlie list-agents
```

#### `charlie info <agent>`

Show detailed information about an agent:

```bash
charlie info claude
charlie info gemini
```

### Library API

Use Charlie programmatically in Python:

```python
from charlie import AgentSpecRegistry, AgentConfiguratorFactory, Tracker
from charlie.config import ProjectConfig, CommandConfig, MCPServerHttpConfig, MCPServerStdioConfig
from charlie.enums import RuleMode

registry = AgentSpecRegistry()

# Create configurator
configurator = AgentConfiguratorFactory.create(
    agent_spec = registry.get("claude"),
    project_config = ProjectConfig(
        name = "My Project",
        namespace = "my",
        dir = "/path/to/project",
    ),
    tracker = Tracker()
)

# Generate commands
command_files = configurator.commands([
    CommandConfig(
        name = "commit",
        description = "Analyze changes and create a high-quality git commit",
        prompt = "Check what changed, and commit your changes. The body of the message explains WHY it changed",
        metadata = {
            "allowed-tools": "Bash(git add:*), Bash(git status:*), Bash(git commit:*)"
        },
        replacements = {}
    ),
    CommandConfig(
        name = "commit",
        description = "Analyze changes and create a high-quality git commit",
        prompt = "Run {{script}}",
        metadata = {},
        replacements = {
          "script": ".claude/assets/script.sh"
        }
    )
])

# Generate MCP configuration
configurator.mcp_servers([
    MCPServerHttpConfig(
        name = "my-mcp-server",
        transport = "http",
        url = "https://example.com/mcp",
        headers = {
            "Authorization": "Bearer F8417EA8-94F3-447C-A108-B0AD7E428BE6",
            "Content-Type": "application/json"
        },
    ),
    MCPServerStdioConfig(
        name = "my-mcp-server",
        transport = "stdio",
        command = "node",
        args = ["npx", "my-command"],
        env = {
            "API_TOKEN": "84EBB71B-0FF8-49D8-84C8-55FF9550CA2C"
        },
    ),
])

# Generate rules
configurator.rules(
    [
        RuleConfig(
            title = "Commit message standards",
            prompt = "Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)",
            metadata = {
                "alwaysApply": True,
            }
        ),
        RuleConfig(
            title = "Coding standards",
            prompt = "All code should follow {{standard}}",
            metadata = {},
            replacements = {
                "standard": "PEP 8"
            }
        )
    ],
    RuleMode.MERGED
)

# Copy assets (if .charlie/assets exists)
configurator.assets()
```

## Supported Agents

Charlie supports 15+ AI agents with built-in knowledge of their requirements:

Run `charlie list-agents` for the complete list.

### Metadata support

Charlie uses **pass-through metadata** - add any agent-specific metadata to your commands or rules, and Charlie will include them in generated output:

Charlie extracts these fields and includes them in agent-specific output (YAML frontmatter for Markdown agents, TOML fields for TOML agents). See [`AGENT_FIELDS.md`](AGENT_FIELDS.md) for details on which agents support which fields.

### Rules Generation Modes

Rules are generated by default in two modes:

**Merged Mode** (default) - Single file with all sections:

```bash
charlie generate cursor --rules-mode merged
```

**Separate Mode** - One file per section:

```bash
charlie generate cursor --rules-mode separate
```

Use merged mode for simple projects, separate mode for better organization in complex projects.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=charlie
```

## Contributing

Contributions welcome! Key areas:

- Adding support for new AI agents
- Improving documentation
- Adding more examples
- Bug fixes and tests

## License

MIT

## Acknowledgments

Charlie was inspired by the need to maintain consistent command definitions across multiple AI agents in the [Spec Kit](https://github.com/github/spec-kit) project.
