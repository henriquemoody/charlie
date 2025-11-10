---
name: "init"
description: "Initialize a new feature"
allowed-tools: Bash(mkdir:*), Bash(touch:*), Bash(echo:*)
tags:
  - initialization
  - setup
category: "project-management"
replacements:
  script:
    discriminator: shell
    options:
      bash: "{{assets_dir}}/init.sh"
      powershell: "{{assets_dir}}/init.ps1"
---

## User Input

{{user_input}}

## Task

Initialize a new feature based on the user's description.

1. Create necessary directory structure
2. Generate boilerplate files
3. Run: {{script}}
