from abc import ABC, abstractmethod
from pathlib import Path

from charlie.enums import ScriptType
from charlie.schema import AgentSpec, Command
from charlie.utils import PlaceholderTransformer


class BaseAgentAdapter(ABC):
    def __init__(self, agent_specification: AgentSpec, root_dir: str = "."):
        self.spec = agent_specification
        self.root_dir = root_dir
        self.transformer = PlaceholderTransformer(agent_specification, root_dir)

    @abstractmethod
    def generate_command(self, command: Command, namespace: str | None, script_type: str) -> str:
        pass

    def generate_commands(self, commands: list[Command], namespace: str | None, output_directory: str) -> list[str]:
        generated_command_files = []
        commands_output_dir = Path(output_directory) / self.spec.command_dir
        commands_output_dir.mkdir(parents=True, exist_ok=True)

        script_type = ScriptType.SH.value

        for command_definition in commands:
            if command_definition.scripts and command_definition.scripts.sh:
                script_type = ScriptType.SH.value
            elif command_definition.scripts and command_definition.scripts.ps:
                script_type = ScriptType.PS.value

            if namespace:
                output_filename = f"{namespace}.{command_definition.name}{self.spec.file_extension}"
            else:
                output_filename = f"{command_definition.name}{self.spec.file_extension}"
            command_file_path = commands_output_dir / output_filename

            print(command_file_path)

            command_content = self.generate_command(command_definition, namespace, script_type)
            command_file_path.write_text(command_content, encoding="utf-8")
            generated_command_files.append(str(command_file_path))

        return generated_command_files

    def transform_placeholders(self, text_content: str, command: Command, script_type: str) -> str:
        return self.transformer.transform(text_content, command, script_type)

    def transform_path_placeholders(self, text_with_paths: str) -> str:
        return self.transformer.transform_path_placeholders(text_with_paths)

    def _get_script_path(self, command: Command, script_type: str) -> str:
        if not command.scripts:
            return ""

        if script_type == ScriptType.SH.value and command.scripts.sh:
            return command.scripts.sh
        elif script_type == ScriptType.PS.value and command.scripts.ps:
            return command.scripts.ps
        return command.scripts.sh or command.scripts.ps or ""

    def _get_agent_script_path(self, command: Command, script_type: str) -> str:
        if not command.agent_scripts:
            return ""

        if script_type == ScriptType.SH.value and command.agent_scripts.sh:
            return command.agent_scripts.sh
        elif script_type == ScriptType.PS.value and command.agent_scripts.ps:
            return command.agent_scripts.ps
        return command.agent_scripts.sh or command.agent_scripts.ps or ""
