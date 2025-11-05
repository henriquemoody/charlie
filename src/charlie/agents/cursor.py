"""Cursor agent adapter."""

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class CursorAdapter(BaseAgentAdapter):
    """Adapter for Cursor commands (Markdown format)."""

    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Generate Cursor command file in Markdown format.

        Args:
            command: Command definition
            namespace: Command namespace/prefix
            script_type: Script type (sh or ps)

        Returns:
            Markdown formatted command content
        """
        # Transform placeholders in prompt
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        # Cursor uses same format as Claude
        frontmatter = f"""---
description: {command.description}
---

"""

        return frontmatter + prompt

