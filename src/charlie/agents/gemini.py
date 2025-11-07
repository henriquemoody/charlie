"""Gemini CLI agent adapter."""

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class GeminiAdapter(BaseAgentAdapter):
    """Adapter for Gemini CLI commands (TOML format)."""

    def generate_command(self, command: Command, namespace: str | None, script_type: str) -> str:
        """Generate Gemini CLI command file in TOML format.

        Args:
            command: Command definition
            namespace: Command namespace/prefix (optional)
            script_type: Script type (sh or ps)

        Returns:
            TOML formatted command content
        """
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        prompt_escaped = prompt.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

        toml_lines = [f'description = "{command.description}"']

        command_dict = command.model_dump()

        core_fields = {"name", "description", "prompt", "scripts", "agent_scripts"}
        for key, value in command_dict.items():
            if key not in core_fields and value is not None:
                if isinstance(value, str):
                    toml_lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    items = ", ".join(
                        f'"{item}"' if isinstance(item, str) else str(item) for item in value
                    )
                    toml_lines.append(f"{key} = [{items}]")
                elif isinstance(value, dict):
                    items = ", ".join(
                        f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}"
                        for k, v in value.items()
                    )
                    toml_lines.append(f"{key} = {{ {items} }}")
                else:
                    toml_lines.append(f"{key} = {value}")

        toml_lines.append("")
        toml_lines.append(f'prompt = """\n{prompt_escaped}\n"""')

        return "\n".join(toml_lines) + "\n"
