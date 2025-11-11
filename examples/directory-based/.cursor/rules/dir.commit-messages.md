---
description: Commit Message Format
---

## Conventional Commits

All commit messages must follow the Conventional Commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style/formatting
- **refactor**: Code refactoring
- **test**: Test updates
- **chore**: Build/tooling changes

### Examples

```
feat(auth): add OAuth2 support

Implement OAuth2 authentication flow using the authorization code grant.

Closes #123
```

```
fix(api): handle null response from upstream service

Add null check before processing API response to prevent crashes.
```