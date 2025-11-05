# Charlie - Universal Command Transpiler

**Define slash commands, MCP servers, and agent rules once in YAML. Generate for any AI agent.**

Charlie is a universal command definition system that transpiles YAML configurations into agent-specific formats for AI assistants, MCP servers, and IDE rules.

[![Tests](https://img.shields.io/badge/tests-94%20passed-green)]()
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

## Features

- ✨ **Single Definition**: Write commands once in YAML
- 🤖 **Multi-Agent Support**: Generate for 15+ AI agents (Claude, Copilot, Cursor, Gemini, Windsurf, and more)
- 🔌 **MCP Integration**: Generate MCP server configurations with tool schemas
- 📋 **Rules Generation**: Create agent-specific rules files with manual preservation
- 🎯 **Auto-Detection**: Automatically finds `charlie.yaml` in current directory
- ⚡ **Runtime Targeting**: Choose which agents to generate for at runtime
- 📦 **Library & CLI**: Use as CLI tool or import as Python library

## Quick Start

### Installation

```bash
# From source (until PyPI release)
pip install -e /path/to/charlie
```

### Create Configuration

Create `charlie.yaml` in your project:

```yaml
version: "1.0"

project:
  name: "my-project"
  command_prefix: "myapp"

mcp_servers:
  - name: "myapp-commands"
    command: "node"
    args: ["dist/mcp-server.js"]

commands:
  - name: "init"
    description: "Initialize a new feature"
    prompt: |
      ## User Input
      
      {{user_input}}
      
      ## Instructions
      
      1. Parse the description
      2. Run: {{script}}
    scripts:
      sh: "scripts/init.sh"
      ps: "scripts/init.ps1"
```

### Generate Outputs

```bash
# Generate for specific agents
charlie generate --agents claude,copilot,gemini

# Generate everything (commands + MCP + rules)
charlie generate --agents claude --mcp --rules

# Generate MCP config only
charlie generate --mcp

# Validate configuration
charlie validate
```

## Usage

### CLI Commands

#### generate

Generate agent-specific configurations:

```bash
# Auto-detect charlie.yaml
charlie generate --agents claude,gemini

# Explicit config file
charlie generate my-config.yaml --agents cursor

# Multiple targets
charlie generate --agents claude,windsurf --mcp --rules

# Custom output directory
charlie generate --agents cursor --output ./build

# Generate all defaults
charlie generate --all
```

#### validate

Validate YAML configuration:

```bash
# Auto-detect charlie.yaml
charlie validate

# Specific file
charlie validate my-config.yaml
```

#### list-agents

List all supported AI agents:

```bash
charlie list-agents
```

#### info

Show detailed information about an agent:

```bash
charlie info claude
charlie info gemini
```

### Library API

Use Charlie programmatically in Python:

```python
from charlie import CommandTranspiler

# Initialize with config
transpiler = CommandTranspiler("charlie.yaml")

# Generate for specific agents
results = transpiler.generate(
    agents=["claude", "copilot"],
    mcp=True,
    rules=True,
    output_dir="./output"
)

# Generate only MCP config
mcp_file = transpiler.generate_mcp("./output")

# Generate only rules
rules_files = transpiler.generate_rules(
    agents=["windsurf", "cursor"],
    output_dir="./output"
)
```

## Supported Agents

Charlie supports 15+ AI agents with built-in knowledge of their requirements:

| Agent | Format | Directory | Notes |
|-------|--------|-----------|-------|
| Claude Code | Markdown | `.claude/commands/` | ✅ Full support |
| GitHub Copilot | Markdown | `.github/prompts/` | ✅ Full support |
| Cursor | Markdown | `.cursor/commands/` | ✅ Full support |
| Gemini CLI | TOML | `.gemini/commands/` | ✅ Full support |
| Qwen Code | TOML | `.qwen/commands/` | ✅ Full support |
| Windsurf | Markdown | `.windsurf/workflows/` | ✅ Full support |
| Kilo Code | Markdown | `.kilocode/workflows/` | ✅ Full support |
| opencode | Markdown | `.opencode/command/` | ✅ Full support |
| Codex CLI | Markdown | `.codex/prompts/` | ✅ Full support |
| Auggie CLI | Markdown | `.augment/commands/` | ✅ Full support |
| Roo Code | Markdown | `.roo/commands/` | ✅ Full support |
| CodeBuddy CLI | Markdown | `.codebuddy/commands/` | ✅ Full support |
| Amp | Markdown | `.agents/commands/` | ✅ Full support |
| Amazon Q Developer | Markdown | `.amazonq/prompts/` | ✅ Full support |

Run `charlie list-agents` for the complete list.

## Configuration

### YAML Schema

```yaml
version: "1.0"  # Schema version

project:
  name: "project-name"
  command_prefix: "prefix"  # Used in /prefix.command-name

# MCP server definitions (optional)
mcp_servers:
  - name: "server-name"
    command: "node"
    args: ["server.js"]
    env:
      KEY: "value"

# Rules configuration (optional)
rules:
  title: "Custom Title"
  include_commands: true
  include_tech_stack: true
  preserve_manual: true

# Command definitions (required)
commands:
  - name: "command-name"
    description: "Command description"
    prompt: |
      Command prompt template
      
      User input: {{user_input}}
      Run: {{script}}
    scripts:
      sh: "path/to/script.sh"
      ps: "path/to/script.ps1"
    agent_scripts:  # Optional agent-specific scripts
      sh: "path/to/agent-script.sh"
```

### Placeholders

Charlie supports these universal placeholders in prompts:

- `{{user_input}}` → Replaced with agent-specific input placeholder (`$ARGUMENTS` or `{{args}}`)
- `{{script}}` → Replaced with the appropriate script path based on platform
- `{{agent_script}}` → Replaced with optional agent-specific script path

## Output Examples

### Agent Command (Markdown)

Generated `.claude/commands/myapp.init.md`:

```markdown
---
description: Initialize a new feature
---

## User Input

```text
$ARGUMENTS
```

## Instructions

1. Parse the description
2. Run: scripts/init.sh
```

### Agent Command (TOML)

Generated `.gemini/commands/myapp.init.toml`:

```toml
description = "Initialize a new feature"

prompt = """
## User Input

{{args}}

## Instructions

1. Parse the description
2. Run: scripts/init.sh
"""
```

### MCP Server Config

Generated `mcp-config.json`:

```json
{
  "mcpServers": {
    "myapp-commands": {
      "command": "node",
      "args": ["dist/mcp-server.js"],
      "capabilities": {
        "tools": {
          "enabled": true,
          "list": [
            {
              "name": "myapp_init",
              "description": "Initialize a new feature",
              "inputSchema": {
                "type": "object",
                "properties": {
                  "input": {"type": "string"}
                },
                "required": ["input"]
              }
            }
          ]
        }
      }
    }
  }
}
```

### Rules File

Generated `.windsurf/rules/charlie-rules.md`:

```markdown
# Development Guidelines

Auto-generated by Charlie from configuration
Last updated: 2025-01-15

## Available Commands

- `/myapp.init` - Initialize a new feature

## Command Reference

### /myapp.init

**Description**: Initialize a new feature

**Usage**: `/myapp.init <input>`

**Scripts**:
- Bash: `scripts/init.sh`
- PowerShell: `scripts/init.ps1`

<!-- MANUAL ADDITIONS START -->
<!-- Your custom rules here - preserved on regeneration -->
<!-- MANUAL ADDITIONS END -->
```

## Examples

See [`examples/`](examples/) directory for complete examples:

- [`examples/simple.yaml`](examples/simple.yaml) - Basic configuration
- [`examples/speckit.yaml`](examples/speckit.yaml) - Spec-kit inspired configuration

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

### Project Structure

```
charlie/
├── src/charlie/          # Main package
│   ├── agents/           # Agent adapters
│   ├── cli.py            # CLI interface
│   ├── transpiler.py     # Core engine
│   ├── mcp.py            # MCP generator
│   ├── rules.py          # Rules generator
│   ├── parser.py         # YAML parser
│   └── schema.py         # Pydantic schemas
├── tests/                # Test suite
├── examples/             # Example configurations
└── README.md
```

## Use Cases

### 1. Unified Command Interface

Define commands once, use across all your AI assistants:

```bash
charlie generate --agents claude,copilot,cursor,gemini
```

### 2. MCP Server Setup

Generate MCP server configurations with tool schemas:

```bash
charlie generate --mcp
```

### 3. IDE Rules Management

Generate and maintain agent rules files with manual preservation:

```bash
charlie generate --agents windsurf,cursor --rules
```

### 4. CI/CD Integration

Generate agent-specific configs during build:

```python
from charlie import CommandTranspiler

transpiler = CommandTranspiler("charlie.yaml")
transpiler.generate(
    agents=["claude", "copilot"],
    mcp=True,
    output_dir="./dist"
)
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

