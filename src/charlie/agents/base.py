"""Base agent adapter class."""

from abc import ABC, abstractmethod
from typing import Dict, List
from pathlib import Path

from charlie.schema import Command


class BaseAgentAdapter(ABC):
    """Base class for all agent adapters."""

    def __init__(self, agent_spec: Dict[str, str]):
        """Initialize adapter with agent specification.

        Args:
            agent_spec: Agent specification from registry
        """
        self.spec = agent_spec

    @abstractmethod
    def generate_command(self, command: Command, namespace: str, script_type: str) -> str:
        """Generate agent-specific command file content.

        Args:
            command: Command definition
            namespace: Command namespace/prefix
            script_type: Script type (sh or ps)

        Returns:
            Generated command file content
        """
        pass

    def generate_commands(
        self, commands: List[Command], namespace: str, output_dir: str
    ) -> List[str]:
        """Generate all command files for this agent.

        Args:
            commands: List of command definitions
            namespace: Command namespace/prefix
            output_dir: Base output directory

        Returns:
            List of generated file paths
        """
        generated_files = []
        command_dir = Path(output_dir) / self.spec["command_dir"]
        command_dir.mkdir(parents=True, exist_ok=True)

        # Determine script type to use (prefer sh, fallback to ps)
        script_type = "sh"  # Default to sh

        for command in commands:
            # Check if command has the preferred script type
            if command.scripts.sh:
                script_type = "sh"
            elif command.scripts.ps:
                script_type = "ps"

            filename = f"{namespace}.{command.name}{self.spec['file_extension']}"
            filepath = command_dir / filename

            content = self.generate_command(command, namespace, script_type)
            filepath.write_text(content, encoding="utf-8")
            generated_files.append(str(filepath))

        return generated_files

    def transform_placeholders(self, text: str, command: Command, script_type: str) -> str:
        """Replace universal placeholders with agent-specific ones.

        Args:
            text: Text with universal placeholders
            command: Command definition
            script_type: Script type (sh or ps)

        Returns:
            Text with agent-specific placeholders
        """
        # Replace user input placeholder
        text = text.replace("{{user_input}}", self.spec["arg_placeholder"])

        # Replace script placeholder with actual script
        script_path = self._get_script_path(command, script_type)
        text = text.replace("{{script}}", script_path)

        # Replace agent script placeholder if present
        if command.agent_scripts:
            agent_script_path = self._get_agent_script_path(command, script_type)
            text = text.replace("{{agent_script}}", agent_script_path)

        return text

    def _get_script_path(self, command: Command, script_type: str) -> str:
        """Get the script path for a command.

        Args:
            command: Command definition
            script_type: Script type (sh or ps)

        Returns:
            Script path
        """
        if script_type == "sh" and command.scripts.sh:
            return command.scripts.sh
        elif script_type == "ps" and command.scripts.ps:
            return command.scripts.ps
        # Fallback: return whatever is available
        return command.scripts.sh or command.scripts.ps or ""

    def _get_agent_script_path(self, command: Command, script_type: str) -> str:
        """Get the agent script path for a command.

        Args:
            command: Command definition
            script_type: Script type (sh or ps)

        Returns:
            Agent script path or empty string if not defined
        """
        if not command.agent_scripts:
            return ""

        if script_type == "sh" and command.agent_scripts.sh:
            return command.agent_scripts.sh
        elif script_type == "ps" and command.agent_scripts.ps:
            return command.agent_scripts.ps
        # Fallback
        return command.agent_scripts.sh or command.agent_scripts.ps or ""

