import yaml

from charlie.agents.base import BaseAgentAdapter
from charlie.schema import Command


class CopilotAdapter(BaseAgentAdapter):
    def generate_command(self, command: Command, namespace: str | None, script_type: str) -> str:
        prompt = self.transform_placeholders(command.prompt, command, script_type)

        command_dict = command.model_dump()

        frontmatter_data = {"description": command.description}

        core_fields = {"name", "description", "prompt", "scripts", "agent_scripts"}
        for key, value in command_dict.items():
            if key not in core_fields and value is not None:
                frontmatter_data[key] = value

        yaml_str = yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False)
        frontmatter = f"---\n{yaml_str}---\n\n"

        return frontmatter + prompt
