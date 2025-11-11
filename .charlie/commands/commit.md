---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Analyze changes and create a high-quality git commit
---

## Context

- Current branch: !`git branch --show-current`
- Working tree status: !`git status --short --branch`
- Unstaged changes: !`git diff`
- Staged changes: !`git diff --cached`
- Recent history (if available): !`git log --oneline -10 || echo "No commits yet"`

## Your task

Analyze the context above and:

1. Summarize the intent of the changes.
2. Explain why those changes are important
3. Commit the changes `git commit -m "<generated message>"`.
4. Add `Assisted-by: {{agent_name}} (<Model>)`
