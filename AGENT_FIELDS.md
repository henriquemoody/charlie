# Agent-Specific Fields Reference

Charlie supports **pass-through fields** - any field you add to commands or rules that isn't a core Charlie field will be passed through to the generated agent-specific output.

This document lists known fields that specific agents support, but you can add any custom field and Charlie will include it in the output.

## Command Fields

### Core Fields (All Agents)

These are Charlie's core command fields and are always processed:

- `name` - Command name
- `description` - Command description
- `prompt` - Command prompt template
- `scripts` - Platform-specific scripts (sh, ps)
- `agent_scripts` - Optional agent-specific scripts

### Agent-Specific Fields

#### Claude Code

```yaml
# Security restrictions
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)

# Organization
tags: ["git", "vcs"]
category: "source-control"
```

**Output Format:** YAML frontmatter in generated `.claude/commands/*.md` files.

**Documentation:** [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)

#### GitHub Copilot

```yaml
# Organization
tags: ["deployment", "ops"]
category: "operations"
```

**Output Format:** YAML frontmatter in generated `.github/prompts/*.prompt.md` files.

**Note:** Copilot's command system is primarily for organization; most fields are for metadata only.

#### Cursor

```yaml
# Organization
tags: ["init", "setup"]
category: "project-management"
```

**Output Format:** YAML frontmatter in generated `.cursor/commands/*.md` files.

#### Gemini CLI / Qwen Code

```yaml
# Organization
tags: ["build", "compile"]
category: "development"
```

**Output Format:** TOML key-value pairs in generated `.gemini/commands/*.toml` or `.qwen/commands/*.toml` files.

**Example Output:**

```toml
description = "Build project"
tags = ["build", "compile"]
category = "development"

prompt = """
Build instructions here
"""
```

## Rules Fields

### Core Fields (All Agents)

These are Charlie's core rules fields and are always processed:

- `title` - Section title
- `content` - Section content (Markdown)
- `order` - Display order (lower numbers first)

### Agent-Specific Fields

#### Cursor

```yaml
# Control when rules apply
alwaysApply: true # or false
globs:
  - "**/*.py"
  - "**/*.ts"
  - "!**/test_*.py" # Exclusion pattern
```

**Output Format:** YAML frontmatter at top of generated `.cursor/rules/*.md` files.

**Behavior:**

- `alwaysApply: true` - Rule applies to all files
- `alwaysApply: false` - Rule applies only to files matching globs
- `globs` - Array of glob patterns (supports negation with `!`)

#### Windsurf

```yaml
# Priority and organization
priority: "high" # or "medium", "low"
categories:
  - "style"
  - "formatting"
  - "best-practices"
```

**Output Format:** Metadata in generated `.windsurf/workflows/*.md` files.

**Behavior:**

- `priority` - Determines rule importance
- `categories` - Tags for organizing rules

#### Kilo Code

```yaml
# Scope control
enabled: true
scope: "workspace" # or "file", "selection"
```

**Output Format:** Metadata in generated `.kilocode/workflows/*.md` files.

## MCP Server Fields

### Core Fields (All Agents)

- `name` - Server name
- `command` - Command to run
- `args` - Command arguments (array)
- `env` - Environment variables (dict)
- `commands` - Commands this server exposes (array)
- `config` - Server-specific configuration (dict)

### Extension Fields

You can add any additional fields to MCP server definitions:

```yaml
name: "my-server"
command: "node"
args: ["server.js"]

# Custom fields
timeout: 30000
retry: 3
port: 3000
version: "1.0.0"
```

These fields are preserved in the generated `mcp-config.json` as custom metadata.

## Field Discovery

Charlie doesn't validate or restrict agent-specific fields - if an agent supports a field, add it to your YAML and Charlie will pass it through.

### Testing New Fields

1. Check agent's documentation for supported fields
2. Add field to your command/rule YAML
3. Generate output: `charlie setup <agent>`
4. Verify field appears in generated output

### Example: Adding New Field

If you discover a new Cursor field like `experimental-feature`:

```yaml
# .charlie/rules/my-rule.yaml
title: "My Rule"
content: "Rule content"
alwaysApply: true
experimental-feature: true # New field
```

Charlie will include it in the output:

```markdown
---
alwaysApply: true
experimental-feature: true
---

# My Rule

Rule content
```

## Limitations and Notes

### Field Name Conversion

Charlie preserves field names as-is, including case:

- `alwaysApply` → `alwaysApply` (camelCase preserved)
- `allowed_tools` → `allowed_tools` (snake_case preserved)
- `allowed-tools` → `allowed-tools` (kebab-case preserved)

### YAML vs TOML Format

**Markdown agents** (Claude, Copilot, Cursor, etc.):

- Extra fields become YAML frontmatter
- Lists formatted as YAML arrays
- Dicts formatted as YAML objects

**TOML agents** (Gemini, Qwen):

- Extra fields become TOML key-value pairs
- Lists formatted as TOML arrays: `[item1, item2]`
- Dicts formatted as inline tables: `{key1 = value1, key2 = value2}`

### Unsupported Fields

If an agent doesn't support a field, it will still appear in the output but may be ignored by the agent. This is by design—Charlie acts as a universal transpiler without enforcing agent-specific validation.

## Contributing

Found a new agent-specific field? Please contribute:

1. Document the field in this file
2. Add example to [`examples/directory-based/`](examples/directory-based/)
3. Submit a pull request

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/)
- [Cursor Rules Documentation](https://cursor.com/docs)
- [GitHub Copilot Prompts](https://docs.github.com/en/copilot)
- [Gemini CLI](https://ai.google.dev/gemini-api/docs)
