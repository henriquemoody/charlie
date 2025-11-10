---
name: "deploy"
description: "Deploy application to specified environment"
replacements:
  script:
    discriminator: shell
    options:
      bash: "{{assets_dir}}/deploy.sh"
      powershell: "{{assets_dir}}/deploy.ps1"
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
