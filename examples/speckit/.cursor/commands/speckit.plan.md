---
description: Execute implementation planning workflow
name: speckit.plan
---

## User Input

$ARGUMENTS

## Outline

1. Setup: Run .specify/scripts/bash/setup-plan.sh --json and parse JSON output
2. Load context: Read feature spec and constitution
3. Execute plan workflow
4. Generate research.md, data-model.md, contracts/
5. Update agent context: .specify/scripts/bash/update-agent-context.sh
6. Report completion

## Key Rules

- Use absolute paths
- ERROR on gate failures
- Resolve all NEEDS CLARIFICATION items
