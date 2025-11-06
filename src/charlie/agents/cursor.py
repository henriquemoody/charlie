"""Cursor agent adapter."""


import yaml

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

        # Extract all fields including pass-through fields
        command_dict = command.model_dump()

        # Build frontmatter with description and any extra fields
        frontmatter_data = {"description": command.description}

        # Add pass-through fields (exclude core Charlie fields)
        core_fields = {"name", "description", "prompt", "scripts", "agent_scripts"}
        for key, value in command_dict.items():
            if key not in core_fields and value is not None:
                frontmatter_data[key] = value

        # Format as YAML frontmatter
        yaml_str = yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False)
        frontmatter = f"---\n{yaml_str}---\n\n"

        return frontmatter + prompt

