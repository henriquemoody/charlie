# AGENTS instructions

This document provides guidelines and instructions for using AI agents effectively.

## Commit messages

- Title
  - Contains 5-116 characters
  - Start with capital letter (A-Z)
  - Use imperative mood ("Add feature" not "Added feature")
  - No ticket numbers (use footer instead)
  - No trailing whitespace
- Body
  - Explain WHY and maybe a bit of HOW
  - Empty line required between title and body
  - Max 116 characters per line (except URLs, code blocks, footer annotations)
  - Minimum 5 characters
- Footer
  - Use trailers:
    - `Ticket: PROJ-1234`
    - `Reference: https://example.com`
    - `Assisted-by: Tool/Agent (<Model/Version>)`
- AI attribution
  - When an AI agent generates/assists with code or commits, add `Assisted-by: Tool/Agent (<Model/Version>)`, for example `Assisted-by: Claude (Claude Sonnet 4.5)`.

