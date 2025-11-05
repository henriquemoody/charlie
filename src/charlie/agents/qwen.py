"""Qwen Code agent adapter."""

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class QwenAdapter(BaseAgentAdapter):
    """Adapter for Qwen Code commands (TOML format)."""

    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Generate Qwen Code command file in TOML format.

        Args:
            command: Command definition
            namespace: Command namespace/prefix
            script_type: Script type (sh or ps)

        Returns:
            TOML formatted command content
        """
        # Transform placeholders in prompt
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        # Escape backslashes and quotes for TOML triple-quoted string
        prompt_escaped = prompt.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

        # Generate TOML format (same as Gemini)
        toml_content = f'''description = "{command.description}"

prompt = """
{prompt_escaped}
"""
'''

        return toml_content

