# Charlie - Universal Agent Config Generator

**Define once in YAML/Markdown. Generate agent-specific commands, MCP config, and rules.**

Charlie is a universal agent configuration generator that produces agent-specific commands, MCP configurations, and rules from a single YAML/Markdown spec.

[![Tests](https://img.shields.io/badge/tests-94%20passed-green)]()
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

## Features

- ✨ **Single Definition**: Write settings once in YAML or Markdown
- 🤖 **Multi-Agent Support**: Generate for different AI agents (Claude, Cursor, and GitHub Copilot supported)
- ⚙️ **Slash Commands Integration**: Generate slash commands from a single definition.
- 🔌 **MCP Integration**: Generate MCP server configurations with tool schemas
- 📋 **Rules Generation**: Create agent-specific rules files with manual preservation
- 🎯 **Auto-Detection**: Automatically finds `charlie.yaml` or `.charlie/` directory
- ⚡ **Runtime Targeting**: Choose which agents to generate for at runtime
- 📦 **Library & CLI**: Use as CLI tool or import as Python library

## Quick Start

### Installation

#### Install via pip

```bash
pip install charlie-agents
```

#### Use Docker

Charlie is available as a Docker image, so you don't need to install Python dependencies:

```bash
# Pull the image from GitHub Container Registry
docker pull ghcr.io/henriquemoody/charlie:latest

# Run charlie commands (mount your project directory)
docker run --rm -v $(pwd):/workspace ghcr.io/henriquemoody/charlie list-agents

# Generate configuration
docker run --rm -v $(pwd):/workspace ghcr.io/henriquemoody/charlie generate claude
```

**Create an alias for convenience:**

Add to your `.bashrc` or `.zshrc`:

```bash
alias charlie='docker run --rm -v $(pwd):/workspace ghcr.io/henriquemoody/charlie'
```

Then use it like the native CLI:

```bash
charlie generate claude
charlie validate
charlie list-agents
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
  mcp_api_token: ~        # It will ask the user to provide an API token, if the environment variable is not set

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
    type: "stdio"
    command: "node"
    args: ["server.js"]
    env:
      KEY: "value"

  - name: "remote_server"
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer {{var:mcp_api_token}}"
      Content-Type: "application/json"

# Rules configuration (rules)
rules:
  - description: "Commit message standards"
    prompt: "Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)"

  - description: "Coding standards"
    prompt: "All code should follow PEP 8"

# Ignore patterns (optional) -- will be added to agent-specific ignore files
ignore_patterns:
  - "*.log"
  - "tmp/"
  - "node_modules/"
```

Charlie will also read `charlie.dist.yaml`, unless you have a `charlie.yaml` in the directory.

See [`examples/`](examples/) directory for complete examples:

- [`examples/simple/`](examples/simple/) - Basic configuration
- [`examples/speckit/`](examples/speckit/) - Spec-kit inspired configuration

### Directory-Based Configuration

For better organization and collaboration, use the directory-based approach. The `charlie.yaml` file is **optional** - if you only have a `.charlie/` directory, Charlie will infer the project name from the directory:

```
project/
├── charlie.yaml                  # Optional: Project metadata (name inferred if omitted)
├── .charlieignore                # Optional: Patterns to exclude from AI agents
└── .charlie/
    ├── commands/
    │   ├── init.yaml             # One file per command (Markdown or YAML supported)
    │   └── deploy.md
    ├── rules/
    │   ├── commit-messages.yaml  # One file per rule (Markdown or YAML supported)
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

**Project Placeholders:**

- `{{project_dir}}` → Resolves to the project root directory
- `{{project_name}}` → Replaced with the project name (e.g., `My Project`)
- `{{project_namespace}}` → Replaced with the project namespace (e.g., `my`)

**Agent Placeholders:**

- `{{agent_name}}` → Replaced with the agent's full name (e.g., `Claude Code`, `Cursor`)
- `{{agent_shortname}}` → Replaced with the agent's short identifier (e.g., `claude`, `cursor`)
- `{{agent_dir}}` → Resolves to agent's base directory (e.g., `.claude`, `.cursor`)
- `{{commands_shorthand_injection}}` → Agent-specific command shorthand (e.g., `$ARGUMENTS` for supported agents)

**Agent Path Placeholders:**

- `{{commands_dir}}` → Resolves to agent's commands directory (e.g., `.claude/commands/`)
- `{{rules_dir}}` → Resolves to agent's rules directory (e.g., `.claude/rules/`)
- `{{rules_file}}` → Resolves to agent's rules file path (e.g., `.claude/rules.md`)
- `{{mcp_file}}` → Resolves to agent's MCP configuration file name (e.g., `mcp.json`)
- `{{assets_dir}}` → Resolves to agent's assets directory (e.g., `.claude/assets`)

**Variable Placeholders:**

- `{{var:VARIABLE_NAME}}` → Replaced with the value of a variable defined in your `charlie.yaml`
  - Variables can be defined in the `variables:` section
  - Use `~` as value to prompt user for input if not set as environment variable
  - Example: `{{var:mcp_api_token}}`
  - Charlie will prompt user for input if variable is not set.

**Environment Variable Placeholders:**

- `{{env:VAR_NAME}}` → Replaced with the value of the environment variable
  - Loads from system environment or `.env` file in root directory
  - Raises `EnvironmentVariableNotFoundError` if variable doesn't exist
  - System environment variables take precedence over `.env` file

**Custom Replacements:**

- Custom placeholders can be defined per-command or per-rule using the `replacements` field
- See the Library API section for examples

These placeholders work in commands, rules, and MCP server configurations (command, args, URL, and headers fields).

## Usage

### CLI Commands

#### `charlie generate <agent>`

Setup agent-specific configurations (generates commands, MCP config, and rules by default):

```bash
# Auto-detect charlie.yaml (generates all artifacts)
charlie generate claude

# Setup without MCP config
charlie generate cursor --no-mcp

# Setup without rules (rules)
charlie generate claude --no-rules

# Setup without commands
charlie generate claude --no-commands

# Explicit config file
charlie generate cursor --config my-config.yaml

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
charlie info cursor
```

### Library API

Use Charlie programmatically in Python:

```python
from charlie import AgentRegistry, AgentConfiguratorFactory, Tracker
from charlie.schema import Project, Command, Rule, HttpMCPServer, StdioMCPServer, ValueReplacement
from charlie.enums import RuleMode

# Initialize registry and get agent
registry = AgentRegistry()
agent = registry.get("claude")

# Create project configuration
project = Project(
    name="My Project",
    namespace="my",
    dir="/path/to/project",
)

# Create configurator
configurator = AgentConfiguratorFactory.create(
    agent=agent,
    project=project,
    tracker=Tracker()
)

# Generate commands
configurator.commands([
    Command(
        name="commit",
        description="Analyze changes and create a high-quality git commit",
        prompt="Check what changed, and commit your changes. The body of the message explains WHY it changed",
        metadata={
            "allowed-tools": "Bash(git add:*), Bash(git status:*), Bash(git commit:*)"
        },
        replacements={}
    ),
    Command(
        name="deploy",
        description="Deploy the application",
        prompt="Run {{script}}",
        metadata={},
        replacements={
            "script": ValueReplacement(
                type="value",
                value=".claude/assets/deploy.sh"
            )
        }
    )
])

# Generate MCP configuration
configurator.mcp_servers([
    HttpMCPServer(
        name="my-http-server",
        type="http",
        url="https://example.com/mcp",
        headers={
            "Authorization": "Bearer F8417EA8-94F3-447C-A108-B0AD7E428BE6",
            "Content-Type": "application/json"
        },
    ),
    StdioMCPServer(
        name="my-stdio-server",
        type="stdio",
        command="node",
        args=["server.js"],
        env={
            "API_TOKEN": "84EBB71B-0FF8-49D8-84C8-55FF9550CA2C"
        },
    ),
])

# Generate rules (rules)
configurator.rules(
    [
        Rule(
            name="commit-messages",
            description="Commit message standards",
            prompt="Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)",
            metadata={
                "alwaysApply": True,
            },
            replacements={}
        ),
        Rule(
            name="coding-standards",
            description="Coding standards",
            prompt="All code should follow {{standard}}",
            metadata={},
            replacements={
                "standard": ValueReplacement(
                    type="value",
                    value="PEP 8"
                )
            }
        )
    ],
    RuleMode.MERGED
)

# Copy assets to the agent's directory
configurator.assets([
    ".charlie/assets/deploy.sh",
])
```

## Supported Agents

Charlie currently supports the following AI agents:

- **Claude Code** (`claude`) - Claude's AI coding assistant
- **Cursor** (`cursor`) - AI-powered code editor
- **GitHub Copilot** (`copilot`) - GitHub's AI pair programmer

Run `charlie list-agents` to see all available agents.

### Metadata support

Charlie uses **pass-through metadata** - add any agent-specific metadata to your commands or rules, and Charlie will include them in generated output:

Charlie extracts these fields and includes them in agent-specific output (YAML frontmatter for Markdown agents, TOML fields for TOML agents). See [`AGENT_FIELDS.md`](AGENT_FIELDS.md) for details on which agents support which fields.

### Rules Generation Modes

Rules (rules) can be generated in two modes:

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

### Use Dev Container (optional)

Open the project in VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Open the project in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Wait for the container to build (first time only)
4. Start coding with all tools pre-configured (pytest, mypy, ruff)

The Dev Container provides a consistent development environment with all dependencies and VS Code extensions pre-installed.

### Developer commands

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest # or `make test`

# Run with coverage
pytest --cov=charlie # or `make test-coverage`

# Run ruff
ruff check . # or `make lint` (`make format` to format the code)

# Run mypy
mypy --install-types --non-interactive src/charlie # or `make analyze`
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
