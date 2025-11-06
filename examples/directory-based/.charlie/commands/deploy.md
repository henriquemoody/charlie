---
name: "deploy"
description: "Deploy application to specified environment"
allowed-tools:
  - Bash(docker:*)
  - Bash(kubectl:*)
  - Bash(helm:*)
tags:
  - deployment
  - production
category: "operations"
scripts:
  sh: "scripts/deploy.sh"
  ps: "scripts/Deploy.ps1"
---

## Deployment Request

{{user_input}}

## Safety Checks

Before deploying:
1. Verify target environment
2. Check for breaking changes
3. Ensure tests pass

## Execute Deployment

Run: {{script}}

