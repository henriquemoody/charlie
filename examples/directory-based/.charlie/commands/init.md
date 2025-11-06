---
name: "init"
description: "Initialize a new feature"
allowed-tools:
  - Bash(mkdir:*)
  - Bash(touch:*)
  - Bash(echo:*)
tags:
  - initialization
  - setup
category: "project-management"
scripts:
  sh: "scripts/init-feature.sh"
  ps: "scripts/Init-Feature.ps1"
---

## User Input

{{user_input}}

## Task

Initialize a new feature based on the user's description.

1. Create necessary directory structure
2. Generate boilerplate files
3. Run: {{script}}

