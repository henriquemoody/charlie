from pathlib import Path

from charlie.enums import ScriptType
from charlie.schema import AgentSpec, Command


class PlaceholderTransformer:
    def __init__(self, agent_spec: AgentSpec, root_dir: str = "."):
        self.agent_spec = agent_spec
        self.root_dir = root_dir

    def transform_path_placeholders(self, text: str) -> str:
        path_placeholders = {
            "{{root}}": self.root_dir,
            "{{agent_dir}}": Path(self.agent_spec.command_dir).parent.as_posix(),
            "{{commands_dir}}": self.agent_spec.command_dir,
            "{{rules_dir}}": Path(self.agent_spec.rules_file).parent.as_posix(),
        }

        transformed_text = text
        for placeholder, replacement in path_placeholders.items():
            transformed_text = transformed_text.replace(placeholder, replacement)

        return transformed_text

    def transform_content_placeholders(self, text: str, command: Command, script_type: str) -> str:
        transformed_text = text.replace("{{user_input}}", self.agent_spec.arg_placeholder)

        script_path = self._get_script_path(command, script_type)
        transformed_text = transformed_text.replace("{{script}}", script_path)

        if command.agent_scripts:
            agent_script_path = self._get_agent_script_path(command, script_type)
            transformed_text = transformed_text.replace("{{agent_script}}", agent_script_path)

        return transformed_text

    def transform(self, text: str, command: Command | None = None, script_type: str | None = None) -> str:
        if command and script_type:
            text = self.transform_content_placeholders(text, command, script_type)

        text = self.transform_path_placeholders(text)

        return text

    def _get_script_path(self, command: Command, script_type: str) -> str:
        """Get the appropriate script path for the command and script type."""
        if not command.scripts:
            return ""

        if script_type == ScriptType.SH.value and command.scripts.sh:
            return command.scripts.sh
        elif script_type == ScriptType.PS.value and command.scripts.ps:
            return command.scripts.ps

        return command.scripts.sh or command.scripts.ps or ""

    def _get_agent_script_path(self, command: Command, script_type: str) -> str:
        """Get the appropriate agent-specific script path for the command and script type."""
        if not command.agent_scripts:
            return ""

        if script_type == ScriptType.SH.value and command.agent_scripts.sh:
            return command.agent_scripts.sh
        elif script_type == ScriptType.PS.value and command.agent_scripts.ps:
            return command.agent_scripts.ps

        return command.agent_scripts.sh or command.agent_scripts.ps or ""
