# Charlie - Universal Command Transpiler

Define slash commands, MCP servers, and agent rules once in YAML. Generate for any AI agent.

## Quick Start

```bash
# Install
pip install charlie

# Create charlie.yaml in your project
charlie init

# Generate for your agents
charlie generate --agents claude,copilot --mcp --rules
```

## Features

- **Single Definition**: Define commands once in YAML
- **Multi-Agent**: Generate for Claude, Copilot, Cursor, Gemini, Windsurf, and more
- **MCP Support**: Generate MCP server configurations
- **Rules Generation**: Create agent-specific rules files
- **Auto-Detection**: Automatically finds `charlie.yaml` in current directory

## Usage

```bash
# Auto-detect charlie.yaml
charlie generate --agents claude,gemini

# Explicit config file
charlie generate my-config.yaml --agents cursor

# Generate MCP configs
charlie generate --mcp

# Generate everything
charlie generate --all

# List supported agents
charlie list-agents
```

## Documentation

See [full documentation](docs/) for detailed usage and API reference.

## License

MIT

