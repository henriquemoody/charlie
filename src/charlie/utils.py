import os
import re
from pathlib import Path

from dotenv import load_dotenv

from charlie.enums import ScriptType
from charlie.schema import AgentSpec, Command


class EnvironmentVariableNotFoundError(Exception):
    pass


class PlaceholderTransformer:
    def __init__(self, agent_spec: AgentSpec, root_dir: str = "."):
        self.agent_spec = agent_spec
        self.root_dir = root_dir

        # Load .env file from root directory if it exists
        env_file = Path(root_dir) / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def transform_agent_placeholders(self, text: str) -> str:
        transformed_text = text.replace("{{user_input}}", self.agent_spec.arg_placeholder)
        transformed_text = transformed_text.replace("{{agent_name}}", self.agent_spec.name)

        return transformed_text

    def transform_env_placeholders(self, text: str) -> str:
        pattern = r"\{\{env:([A-Za-z_][A-Za-z0-9_]*)\}\}"

        def replace_env(match: re.Match[str]) -> str:
            var_name = match.group(1)
            value = os.getenv(var_name)

            if value is None:
                raise EnvironmentVariableNotFoundError(
                    f"Environment variable '{var_name}' not found. Make sure it's set in your environment or .env file."
                )

            return value

        return re.sub(pattern, replace_env, text)

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

    def transform_command_placeholders(self, text: str, command: Command, script_type: str) -> str:
        script_path = self._get_script_path(command, script_type)
        transformed_text = text.replace("{{script}}", script_path)

        if command.agent_scripts:
            agent_script_path = self._get_agent_script_path(command, script_type)
            transformed_text = transformed_text.replace("{{agent_script}}", agent_script_path)

        return transformed_text

    def transform(self, text: str, command: Command | None = None, script_type: str | None = None) -> str:
        if command and script_type:
            text = self.transform_command_placeholders(text, command, script_type)

        text = self.transform_agent_placeholders(text)
        text = self.transform_path_placeholders(text)
        text = self.transform_env_placeholders(text)

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
