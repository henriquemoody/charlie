"""Claude Code agent adapter."""

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class ClaudeAdapter(BaseAgentAdapter):
    """Adapter for Claude Code commands (Markdown format)."""

    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Generate Claude Code command file in Markdown format.

        Args:
            command: Command definition
            namespace: Command namespace/prefix
            script_type: Script type (sh or ps)

        Returns:
            Markdown formatted command content
        """
        # Transform placeholders in prompt
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        # Generate frontmatter
        frontmatter = f"""---
description: {command.description}
---

"""

        return frontmatter + prompt

