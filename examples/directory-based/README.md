# Directory-Based Configuration Example

This example demonstrates the directory-based configuration approach for Charlie.

## Structure

```
directory-based/
├── charlie.yaml              # Project metadata only
└── .charlie/
    ├── commands/
    │   ├── init.yaml         # Individual command definitions
    │   └── deploy.yaml
    ├── rules/
    │   ├── commit-messages.yaml  # Individual rule sections
    │   ├── code-style.yaml
    │   └── testing.yaml
    └── mcp-servers/
        └── local-tools.yaml  # MCP server configurations
```

## Features Demonstrated

### Agent-Specific Fields

Commands include agent-specific metadata:
- **allowed-tools** (Claude): Restricts command to specific shell operations
- **tags**, **category**: Generic metadata for organization

Rules include agent-specific metadata:
- **alwaysApply**, **globs** (Cursor): Control when rules apply
- **priority**, **categories** (Windsurf): Rule organization

### Generation Modes

Generate with **merged** mode (single rules file):
```bash
charlie generate --agents cursor --rules --rules-mode merged
```

Generate with **separate** mode (one file per section):
```bash
charlie generate --agents cursor --rules --rules-mode separate
```

## Benefits

- **Organization**: Each command and rule in its own file
- **Collaboration**: No merge conflicts on single file
- **Flexibility**: Easy to add/remove commands
- **Maintainability**: Clear structure for large projects

## Try It

```bash
# Navigate to this directory
cd examples/directory-based

# Generate for Claude with allowed-tools support
charlie generate --agents claude --mcp

# Generate for Cursor with globs and alwaysApply support
charlie generate --agents cursor --rules --rules-mode merged

# Generate everything
charlie generate --agents claude,cursor --mcp --rules
```

