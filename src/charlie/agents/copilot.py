"""GitHub Copilot agent adapter."""

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class CopilotAdapter(BaseAgentAdapter):
    """Adapter for GitHub Copilot prompts (Markdown format)."""

    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Generate GitHub Copilot prompt file in Markdown format.

        Args:
            command: Command definition
            namespace: Command namespace/prefix
            script_type: Script type (sh or ps)

        Returns:
            Markdown formatted prompt content
        """
        # Transform placeholders in prompt
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        # Copilot uses same format as Claude
        frontmatter = f"""---
description: {command.description}
---

"""

        return frontmatter + prompt

