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

        # Start with description
        toml_lines = [f'description = "{command.description}"']
        
        # Extract all fields including pass-through fields
        command_dict = command.model_dump()
        
        # Add pass-through fields (exclude core Charlie fields)
        core_fields = {"name", "description", "prompt", "scripts", "agent_scripts"}
        for key, value in command_dict.items():
            if key not in core_fields and value is not None:
                # Format value based on type
                if isinstance(value, str):
                    toml_lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    # Format list as TOML array
                    items = ', '.join(f'"{item}"' if isinstance(item, str) else str(item) for item in value)
                    toml_lines.append(f'{key} = [{items}]')
                elif isinstance(value, dict):
                    # Format dict as inline table
                    items = ', '.join(f'{k} = "{v}"' if isinstance(v, str) else f'{k} = {v}' for k, v in value.items())
                    toml_lines.append(f'{key} = {{ {items} }}')
                else:
                    toml_lines.append(f'{key} = {value}')
        
        # Add prompt at the end
        toml_lines.append('')
        toml_lines.append(f'prompt = """\n{prompt_escaped}\n"""')
        
        return '\n'.join(toml_lines) + '\n'

