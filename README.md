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
- 🎯 **Auto-Detection**: Automatically finds `charlie.yaml` or `.charlie/` directory
- 🚀 **Zero Config**: Works without any configuration file - infers project name from directory
- ⚡ **Runtime Targeting**: Choose which agents to generate for at runtime
- 📦 **Library & CLI**: Use as CLI tool or import as Python library

## Quick Start

### Installation

```bash
pip install charlie-agents
```

### Create Configuration (Optional)

Charlie works without any configuration file! It will infer your project name from the directory name. 

For advanced features, create `charlie.yaml` in your project:

```yaml
version: "1.0"  # Optional, defaults to "1.0"

project:
  name: "my-project"      # Optional, inferred from directory name
  command_prefix: "myapp" # Optional, omit for simple command names

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

**What's Optional?**
- The entire `charlie.yaml` file (project name inferred from directory)
- `project.name` field (inferred from directory name)
- `project.command_prefix` (commands use simple names like `init.md` instead of `myapp.init.md`)

### Generate Outputs

```bash
# Setup for specific agent
charlie setup claude

# Setup with rules
charlie setup cursor --rules

# Setup with MCP and rules
charlie setup claude --mcp --rules

# Validate configuration
charlie validate
```

## Usage

### CLI Commands

#### setup

Setup agent-specific configurations:

```bash
# Auto-detect charlie.yaml
charlie setup claude

# Explicit config file
charlie setup gemini --config my-config.yaml

# Setup with MCP and rules
charlie setup claude --mcp --rules

# Custom output directory
charlie setup cursor --output ./build
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

# Setup for Claude with MCP and rules
results = transpiler.generate(
    agent="claude",
    mcp=True,
    rules=True,
    output_dir="./output"
)

# Setup for Gemini with rules
results = transpiler.generate(
    agent="gemini",
    rules=True,
    output_dir="./output"
)

# Generate only MCP config
mcp_file = transpiler.generate_mcp("./output")

# Generate only rules for an agent
rules_files = transpiler.generate_rules(
    agent="cursor",
    output_dir="./output"
)
```

## Supported Agents

Charlie supports 15+ AI agents with built-in knowledge of their requirements:

| Agent              | Format   | Directory              | Notes           |
| ------------------ | -------- | ---------------------- | --------------- |
| Claude Code        | Markdown | `.claude/commands/`    | ✅ Full support |
| GitHub Copilot     | Markdown | `.github/prompts/`     | ✅ Full support |
| Cursor             | Markdown | `.cursor/commands/`    | ✅ Full support |
| Gemini CLI         | TOML     | `.gemini/commands/`    | ✅ Full support |
| Qwen Code          | TOML     | `.qwen/commands/`      | ✅ Full support |
| Windsurf           | Markdown | `.windsurf/workflows/` | ✅ Full support |
| Kilo Code          | Markdown | `.kilocode/workflows/` | ✅ Full support |
| opencode           | Markdown | `.opencode/command/`   | ✅ Full support |
| Codex CLI          | Markdown | `.codex/prompts/`      | ✅ Full support |
| Auggie CLI         | Markdown | `.augment/commands/`   | ✅ Full support |
| Roo Code           | Markdown | `.roo/commands/`       | ✅ Full support |
| CodeBuddy CLI      | Markdown | `.codebuddy/commands/` | ✅ Full support |
| Amp                | Markdown | `.agents/commands/`    | ✅ Full support |
| Amazon Q Developer | Markdown | `.amazonq/prompts/`    | ✅ Full support |

Run `charlie list-agents` for the complete list.

## Configuration

Charlie is **zero-config by default** - it works without any configuration file and infers the project name from your directory name.

For advanced features, Charlie supports two configuration approaches:

1. **Monolithic** - Single `charlie.yaml` file (good for small projects)
2. **Directory-Based** - Modular files in `.charlie/` directories (good for large projects)

### Directory-Based Configuration (Recommended)

For better organization and collaboration, use the directory-based approach. The `charlie.yaml` file is **optional** - if you only have a `.charlie/` directory, Charlie will infer the project name from the directory:

```
project/
├── charlie.yaml              # Optional: Project metadata (name inferred if omitted)
└── .charlie/
    ├── commands/
    │   ├── init.md          # One file per command (markdown with frontmatter)
    │   └── deploy.md
    ├── rules/
    │   ├── commit-messages.md  # One file per rule section (markdown with frontmatter)
    │   └── code-style.md
    └── mcp-servers/
        └── local-tools.yaml    # MCP servers still use YAML
```

**Benefits:**

- Clear organization (one file per command/rule)
- No merge conflicts on single file
- Easy to add/remove components
- Better for version control diffs
- Native markdown support for rich documentation

**Command File** (`.charlie/commands/init.md`):

```markdown
---
name: "init"
description: "Initialize feature"
allowed-tools: Bash(mkdir:*) # Claude-specific
tags: ["init", "setup"]
category: "project"
scripts:
  sh: "scripts/init.sh"
---

## User Input

{{user_input}}

## Instructions

Initialize the feature and run: {{script}}
```

**Rules File** (`.charlie/rules/code-style.md`):

```markdown
---
title: "Code Style"
order: 1
alwaysApply: true  # Cursor-specific
globs: ["**/*.py"]  # Cursor-specific
priority: "high"    # Windsurf-specific
---

## Formatting

Use Black for formatting with max line length: 100.
```

See [`examples/directory-based/`](examples/directory-based/) for a complete example.

### Monolithic YAML Schema

For simpler projects, use a single `charlie.yaml` file. All fields are optional:

```yaml
version: "1.0" # Optional: Schema version (defaults to "1.0")

project:
  name: "project-name"     # Optional: Inferred from directory name if omitted
  command_prefix: "prefix" # Optional: Used in /prefix.command-name, omit for simple names

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
    agent_scripts: # Optional agent-specific scripts
      sh: "path/to/agent-script.sh"
```

### Placeholders

Charlie supports these universal placeholders in commands and rules:

**Content Placeholders:**

- `{{user_input}}` → Replaced with agent-specific input placeholder (`$ARGUMENTS` or `{{args}}`)
- `{{script}}` → Replaced with the appropriate script path based on platform
- `{{agent_script}}` → Replaced with optional agent-specific script path

**Path Placeholders:**

- `{{root}}` → Resolves to the project root directory
- `{{agent_dir}}` → Resolves to agent's base directory (e.g., `.claude`, `.cursor`)
- `{{commands_dir}}` → Resolves to agent's commands directory (e.g., `.claude/commands/`)
- `{{rules_dir}}` → Resolves to agent's rules directory (e.g., `.claude/rules/`)

These path placeholders are especially useful in rules content when referencing agent-specific locations.

### Agent-Specific Fields

Charlie uses **pass-through fields** - add any agent-specific field to your commands or rules, and Charlie will include them in generated output:

**Command Fields:**

```yaml
# Claude-specific
allowed-tools: Bash(git add:*), Bash(git commit:*)

# Generic metadata
tags: ["git", "vcs"]
category: "source-control"
```

**Rules Fields:**

```yaml
# Cursor-specific
alwaysApply: true
globs: ["**/*.py", "!**/test_*.py"]

# Windsurf-specific
priority: "high"
categories: ["style", "formatting"]
```

Charlie extracts these fields and includes them in agent-specific output (YAML frontmatter for Markdown agents, TOML fields for TOML agents). See [`AGENT_FIELDS.md`](AGENT_FIELDS.md) for details on which agents support which fields.

### Rules Generation Modes

Generate rules files in two modes:

**Merged Mode** (default) - Single file with all sections:

```bash
charlie setup cursor --rules --rules-mode merged
```

**Separate Mode** - One file per section:

```bash
charlie setup cursor --rules --rules-mode separate
```

Use merged mode for simple projects, separate mode for better organization in complex projects.

## Output Examples

### Agent Command (Markdown)

Generated `.claude/commands/myapp.init.md`:

````markdown
---
description: Initialize a new feature
---

## User Input

```text
$ARGUMENTS
```
````

## Instructions

1. Parse the description
2. Run: scripts/init.sh

````

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
````

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
                  "input": { "type": "string" }
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

Define commands once, setup for any AI assistant:

```bash
charlie setup claude
charlie setup copilot
charlie setup cursor
```

### 2. MCP Server Setup

Setup agent with MCP server configurations:

```bash
charlie setup claude --mcp
```

### 3. IDE Rules Management

Setup agent with rules files:

```bash
charlie setup windsurf --rules
charlie setup cursor --rules
```

### 4. CI/CD Integration

Setup agent-specific configs during build:

```python
from charlie import CommandTranspiler

transpiler = CommandTranspiler("charlie.yaml")

# Setup for Claude
transpiler.generate(
    agent="claude",
    mcp=True,
    output_dir="./dist"
)

# Setup for Copilot
transpiler.generate(
    agent="copilot",
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
