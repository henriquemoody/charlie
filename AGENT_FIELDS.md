# Agent-Specific Fields Reference

Charlie supports **pass-through metadata** - any metadata field you add to commands or rules that isn't a core Charlie field will be passed through to the generated agent-specific output.

This document lists known metadata fields that specific agents support, but you can add any custom metadata field and Charlie will include it in the output.

## Supported Agents

Charlie currently supports:

- **Claude Code** (`claude`)
- **Cursor** (`cursor`)
- **GitHub Copilot** (`copilot`)
- **OpenCode** (`opencode`)

## Command Fields

### Core Fields (All Agents)

These are Charlie's core command fields and are always processed:

- `name` - Command name (required)
- `description` - Command description (required)
- `prompt` - Command prompt template (required)
- `metadata` - Dictionary of agent-specific metadata fields (optional)
- `replacements` - Custom placeholder replacements (optional)

### Agent-Specific Metadata Fields

Metadata fields are added under the `metadata` key in your command definition:

```yaml
commands:
  - name: "commit"
    description: "Create a git commit"
    prompt: "Commit your changes..."
    metadata:
      # Agent-specific fields go here
      allowed-tools: "Bash(git add:*), Bash(git status:*)"
      tags: ["git", "vcs"]
```

#### Claude Code

Claude Code supports the following metadata fields:

```yaml
metadata:
  # Security restrictions
  allowed-tools: "Bash(git add:*), Bash(git status:*), Bash(git commit:*)"

  # Organization
  tags: ["git", "vcs"]
  category: "source-control"
```

**Output Format:** YAML frontmatter in generated `.claude/commands/*.md` files.

**Documentation:** [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)

#### Cursor

Cursor supports the following metadata fields:

```yaml
metadata:
  # Organization
  tags: ["init", "setup"]
  category: "project-management"
```

**Output Format:** YAML frontmatter in generated `.cursor/commands/*.md` files.

**Documentation:** [Cursor Commands](https://cursor.com/docs)

#### GitHub Copilot

GitHub Copilot supports the following metadata fields:

```yaml
metadata:
  # Organization
  tags: ["git", "vcs"]
  category: "source-control"
```

**Output Format:** YAML frontmatter in generated `.github/prompts/*.prompt.md` files.

**Documentation:** [GitHub Copilot Prompt Files](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file)

**Note:** GitHub Copilot doesn't have native slash command support like Claude or Cursor. Instead, Charlie generates prompt files and creates an instructions file that lists available commands for reference.

#### OpenCode

OpenCode supports the following metadata fields:

```yaml
metadata:
  # Organization
  description: "Skill description"
```

**Output Format:** YAML frontmatter in generated `.opencode/skills/*.md` files.

**Documentation:** OpenCode treats commands as skills, generating them in the same format.

## Rule Fields (Rules)

### Core Fields (All Agents)

These are Charlie's core rule fields and are always processed:

- `name` - Rule name (required, auto-generated from description if omitted)
- `description` - Rule description/title (required)
- `prompt` - Rule content in Markdown (required)
- `metadata` - Dictionary of agent-specific metadata fields (optional)
- `replacements` - Custom placeholder replacements (optional)

### Agent-Specific Metadata Fields

Metadata fields are added under the `metadata` key in your rule definition:

```yaml
rules:
  - name: "coding-standards"
    description: "Coding standards"
    prompt: "All code should follow PEP 8..."
    metadata:
      # Agent-specific fields go here
      alwaysApply: true
      globs: ["**/*.py"]
```

#### Cursor

Cursor supports the following metadata fields for rules (rules):

```yaml
metadata:
  # Control when rules apply
  alwaysApply: true # Rule applies to all files (default: false)

  # File pattern matching
  globs:
    - "**/*.py"
    - "**/*.ts"
    - "!**/test_*.py" # Exclusion pattern
```

**Output Format:** YAML frontmatter at top of generated `.cursor/rules/*.md` files.

**Behavior:**

- `alwaysApply: true` - Rule applies to all files in the workspace
- `alwaysApply: false` - Rule applies only to files matching the `globs` patterns
- `globs` - Array of glob patterns (supports negation with `!` prefix)

**Documentation:** [Cursor Rules](https://cursor.com/docs)

#### Claude Code

Claude Code doesn't currently support special metadata for rules. Rules are stored as `.claude/rules/*.md` files or in the `CLAUDE.md` file at the project root.

#### GitHub Copilot

GitHub Copilot supports instructions files (files matching the pattern `*instructions.md`):

```yaml
metadata:
  # File pattern matching
  applyTo: "**/*.ts,**/*.tsx"

  # Organization
  description: "Coding standards for this project"
```

**Output Format:**

- **Merged mode**: Single `copilot-instructions.md` file with all rules
- **Separate mode**: Individual `*-instructions.md` files in `.github/instructions/` directory

**Behavior:**

- `applyTo` - Comma-separated string of glob patterns that control which files this instruction applies to (e.g., `"**/*.ts,**/*.tsx"`)

**Documentation:** [GitHub Copilot Repository Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)

**Note:** GitHub Copilot scans the repository for files matching the pattern `*instructions.md`. When using separate mode, Charlie creates individual instruction files and a main instruction file that references them.

#### OpenCode

OpenCode uses custom instructions for rules:

**Output Format:**

- **Merged mode**: Single `instructions.md` file in `.opencode/instructions/`
- **Separate mode**: Individual instruction files in `.opencode/instructions/`

Both modes register instructions in `opencode.json` under the `"instructions"` array.

**Note:** OpenCode does not use metadata fields for rules. Instructions are stored as plain Markdown files.

## Subagent Fields

### Core Fields (All Agents)

These are Charlie's core subagent fields and are always processed:

- `name` - Subagent name in lowercase with hyphens (required, auto-generated from filename if omitted)
- `description` - When the agent should delegate to this subagent (required)
- `prompt` - System prompt that guides the subagent's behavior (the Markdown body when using file-based definitions)
- `metadata` - Dictionary of agent-specific metadata fields (optional)
- `replacements` - Custom placeholder replacements (optional)

### Agent-Specific Metadata Fields

#### Claude Code

Claude Code supports the following metadata fields for subagents:

```yaml
subagents:
  - name: code-reviewer
    description: Expert code reviewer. Use proactively after code changes.
    prompt: You are a senior code reviewer...
    metadata:
      # Tool access control
      tools: "Read, Grep, Glob, Bash" # Allowlist of tools the subagent can use
      disallowedTools: "Write, Edit" # Denylist (removed from allowed set)

      # Model selection
      model: sonnet # sonnet | opus | haiku | inherit (default: inherit)

      # Permission and execution control
      permissionMode: acceptEdits # default | acceptEdits | dontAsk | bypassPermissions | plan
      maxTurns: 10 # Maximum agentic turns before stopping
      background: false # Run as a background task (default: false)
      isolation: worktree # Run in a temporary git worktree (default: none)

      # Knowledge and context
      skills: # Skills to preload into the subagent's context
        - api-conventions
        - error-handling-patterns
      memory: project # Persistent memory scope: user | project | local

      # MCP servers available to this subagent
      mcpServers:
        - slack

      # Lifecycle hooks scoped to this subagent
      hooks:
        PreToolUse:
          - matcher: "Bash"
            hooks:
              - type: command
                command: "./scripts/validate.sh"
```

**Output format:** YAML frontmatter in `.claude/agents/{name}.md`

**Documentation:** [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)

#### Cursor

Cursor supports the following metadata fields for subagents:

```yaml
subagents:
  - name: code-reviewer
    description: Reviews code for quality and best practices
    prompt: You are a code reviewer...
    metadata:
      model: inherit # fast | inherit | or a specific model ID
      readonly: true # Restrict write permissions (default: false)
      is_background: false # Run asynchronously (default: false)
```

**Output format:** YAML frontmatter in `.cursor/agents/{name}.md`

**Documentation:** [Cursor Subagents](https://cursor.com/docs/context/subagents)

#### GitHub Copilot

GitHub Copilot does not have native subagent support. Charlie logs a skip message and generates no output.

#### OpenCode

OpenCode supports the following metadata fields for subagents:

```yaml
subagents:
  - name: code-reviewer
    description: Expert code reviewer. Use proactively after code changes.
    prompt: You are a senior code reviewer...
    metadata:
      # Tool access control
      tools: "Read, Grep, Glob, Bash"

      # Model selection
      model: sonnet # Model identifier

      # Permission control
      permission: default # default | allowed-tools | bypass-permissions
```

**Output format:** YAML frontmatter in `.opencode/agents/{name}.md`

**Note:** OpenCode subagent files include `name` and `description` in the frontmatter along with any supported metadata fields.

## MCP Server Fields

### Core Fields (All Agents)

MCP servers support two transport types:

#### stdio Transport

```yaml
mcp_servers:
  - name: "my-server" # Server name (required)
    type: "stdio" # Transport type (default: "stdio")
    command: "node" # Command to run (required)
    args: ["server.js"] # Command arguments (optional, default: [])
    env: # Environment variables (optional, default: {})
      API_KEY: "value"
```

#### http Transport

```yaml
mcp_servers:
  - name: "remote-server" # Server name (required)
    type: "http" # Transport type
    url: "https://example.com" # Server URL (required)
    headers: # HTTP headers (optional, default: {})
      Authorization: "Bearer token"
      Content-Type: "application/json"
```

**Output Format:** Generated as JSON in `.claude/mcp.json` or `.cursor/mcp.json`

**Note:** Charlie doesn't support custom metadata fields for MCP servers. All fields are part of the MCP specification.

### OpenCode MCP Configuration

OpenCode uses a different MCP configuration format stored in `opencode.json`:

#### stdio Transport (local)

```yaml
mcp_servers:
  - name: "my-server"
    type: "stdio"
    command: "node"
    args: ["server.js"]
    env:
      API_KEY: "value"
```

Generates:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["node", "server.js"],
      "environment": {
        "API_KEY": "value"
      }
    }
  }
}
```

#### http Transport (remote)

```yaml
mcp_servers:
  - name: "remote-server"
    type: "http"
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer token"
      Content-Type: "application/json"
```

Generates:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "remote-server": {
      "type": "remote",
      "url": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer token",
        "Content-Type": "application/json"
      }
    }
  }
}
```

**Key differences from Claude/Cursor:**

- Configuration stored in `opencode.json` (not `mcp.json`)
- Commands stored as arrays: `"command": ["node", "server.js"]`
- Environment variables under `"environment"` key
- Server type is `"local"` (not `"stdio"`)

## Skills

Skills in Charlie are passed through to agents that support them.

### OpenCode

OpenCode treats all skills the same way as commands:

```yaml
skills:
  - name: explain-code
    description: Explains code with visual diagrams and analogies
    prompt: |
      When explaining code, always include an analogy, an ASCII diagram, and a step-by-step walkthrough.
```

**Output format:** YAML frontmatter in `.opencode/skills/{name}/SKILL.md`

**Supported metadata:**

- `description` - Skill description (required)
- `license` - License information
- `compatibility` - Compatibility information

## Field Discovery

Charlie doesn't validate or restrict agent-specific metadata fields - if an agent supports a metadata field, add it to your YAML and Charlie will pass it through.

### Testing New Metadata Fields

1. Check agent's documentation for supported metadata fields
2. Add field to your command/rule `metadata` section
3. Generate output: `charlie generate <agent>`
4. Verify field appears in generated output

### Example: Adding New Metadata Field

If you discover a new Cursor metadata field like `experimental-feature`:

```yaml
# .charlie/rules/my-rule.yaml
name: "my-rule"
description: "My Rule"
prompt: "Rule content here..."
metadata:
  alwaysApply: true
  experimental-feature: true # New metadata field
```

Charlie will include it in the output:

```markdown
---
alwaysApply: true
experimental-feature: true
---

# My Rule

Rule content here...
```

## Limitations and Notes

### Metadata Field Name Preservation

Charlie preserves metadata field names as-is, including case:

- `alwaysApply` → `alwaysApply` (camelCase preserved)
- `allowed_tools` → `allowed_tools` (snake_case preserved)
- `allowed-tools` → `allowed-tools` (kebab-case preserved)

### Output Format

**Both Claude and Cursor** use Markdown format:

- Metadata fields become YAML frontmatter
- Lists formatted as YAML arrays
- Dicts formatted as YAML objects

Example:

```yaml
# Input
metadata:
  tags: ["python", "testing"]
  alwaysApply: true


# Output (YAML frontmatter)
---
tags:
  - python
  - testing
alwaysApply: true
---
```

### Unsupported Metadata Fields

If an agent doesn't support a metadata field, it will still appear in the output but may be ignored by the agent. This is by design—Charlie acts as a universal transpiler without enforcing agent-specific validation.

## Contributing

Found a new agent-specific metadata field? Please contribute:

1. Document the metadata field in this file under the appropriate agent section
2. Add example to [`examples/directory-based/`](examples/directory-based/)
3. Submit a pull request

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/)
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Cursor Documentation](https://cursor.com/docs)
- [MCP (Model Context Protocol) Documentation](https://modelcontextprotocol.io/)
- [OpenCode Documentation](https://opencode.ai)
