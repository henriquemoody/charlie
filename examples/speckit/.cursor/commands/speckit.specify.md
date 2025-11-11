---
description: Create or update feature specification from natural language
name: speckit.specify
---

## User Input

$ARGUMENTS

## Outline

The text after `/speckit.specify` is the feature description.

Given that description:

1. Generate a concise short name (2-4 words)
2. Check for existing branches
3. Run script: .specify/scripts/bash/create-new-feature.sh --json
4. Load spec template
5. Fill in specification sections
6. Write to spec file

## Guidelines

- Focus on WHAT users need and WHY
- Avoid HOW to implement (no tech stack details)
- Written for business stakeholders
