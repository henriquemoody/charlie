"""Base agent adapter class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from charlie.schema import Command


class BaseAgentAdapter(ABC):
    """Base class for all agent adapters."""

    def __init__(self, agent_spec: dict[str, Any], root_dir: str = "."):
        """Initialize adapter with agent specification.

        Args:
            agent_spec: Agent specification from registry
            root_dir: Root directory where charlie.yaml is located
        """
        self.spec = agent_spec
        self.root_dir = root_dir

    @abstractmethod
    def generate_command(self, command: Command, namespace: str | None, script_type: str) -> str:
        """Generate agent-specific command file content.

        Args:
            command: Command definition
            namespace: Command namespace/prefix (optional)
            script_type: Script type (sh or ps)

        Returns:
            Generated command file content
        """
        pass

    def generate_commands(
        self, commands: list[Command], namespace: str | None, output_dir: str
    ) -> list[str]:
        """Generate all command files for this agent.

        Args:
            commands: List of command definitions
            namespace: Command namespace/prefix (optional)
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
            if command.scripts and command.scripts.sh:
                script_type = "sh"
            elif command.scripts and command.scripts.ps:
                script_type = "ps"

            # Build filename with or without namespace
            if namespace:
                filename = f"{namespace}.{command.name}{self.spec['file_extension']}"
            else:
                filename = f"{command.name}{self.spec['file_extension']}"
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

        # Replace path placeholders
        text = self.transform_path_placeholders(text)

        return text

    def transform_path_placeholders(self, text: str) -> str:
        """Replace path placeholders with agent-specific directory paths.

        Args:
            text: Text with path placeholders

        Returns:
            Text with resolved paths
        """
        # Replace root directory placeholder
        text = text.replace("{{root}}", self.root_dir)

        # Get the base agent directory (e.g., ".claude", ".cursor")
        agent_dir = Path(self.spec.get("command_dir", "")).parent

        # Replace agent directory placeholder
        # Use as_posix() for consistent forward slashes across platforms
        text = text.replace("{{agent_dir}}", agent_dir.as_posix())

        # Replace commands directory placeholder
        commands_dir = self.spec.get("command_dir", "")
        text = text.replace("{{commands_dir}}", commands_dir)

        # Replace rules directory placeholder (if rules_file is defined)
        if "rules_file" in self.spec:
            rules_dir = Path(self.spec["rules_file"]).parent.as_posix()
            text = text.replace("{{rules_dir}}", rules_dir)
        else:
            # Fallback: use common pattern
            # Use as_posix() for consistent forward slashes across platforms
            text = text.replace("{{rules_dir}}", (agent_dir / "rules").as_posix())

        return text

    def _get_script_path(self, command: Command, script_type: str) -> str:
        """Get the script path for a command.

        Args:
            command: Command definition
            script_type: Script type (sh or ps)

        Returns:
            Script path
        """
        if not command.scripts:
            return ""

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
