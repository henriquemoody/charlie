import os
import re
from pathlib import Path

from dotenv import load_dotenv

from charlie.enums import ScriptType
from charlie.schema import (
    AgentSpec,
    Command,
    MCPServerHttpConfig,
    MCPServerStdioConfig,
    ProjectConfig,
    RulesSection,
)


class EnvironmentVariableNotFoundError(Exception):
    pass


class PlaceholderTransformer:
    def __init__(
        self,
        agent_spec: AgentSpec,
        root_dir: str = ".",
        variables: dict[str, str] | None = None,
        project_config: ProjectConfig | None = None,
    ):
        self.agent_spec = agent_spec
        self.root_dir = root_dir
        self.variables = variables or {}
        self.project_config = project_config

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
            "{{rules_dir}}": self.agent_spec.rules_dir,
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

    def command(self, cmd: Command, script_type: str = "sh") -> Command:
        transformed_prompt = self.transform(cmd.prompt, cmd, script_type)

        return Command(
            name=cmd.name,
            description=cmd.description,
            prompt=transformed_prompt,
            scripts=cmd.scripts,
            agent_scripts=cmd.agent_scripts,
            **{k: v for k, v in cmd.model_extra.items()} if cmd.model_extra else {},
        )

    def rule(self, rule_section: RulesSection) -> RulesSection:
        transformed_content = self.transform_agent_placeholders(rule_section.content)
        transformed_content = self.transform_path_placeholders(transformed_content)
        transformed_content = self.transform_env_placeholders(transformed_content)

        return RulesSection(
            title=rule_section.title,
            content=transformed_content,
            order=rule_section.order,
            filename=rule_section.filename,
            **{k: v for k, v in rule_section.model_extra.items()} if rule_section.model_extra else {},
        )

    def mcp_server(
        self, server: MCPServerStdioConfig | MCPServerHttpConfig
    ) -> MCPServerStdioConfig | MCPServerHttpConfig:
        if isinstance(server, MCPServerStdioConfig):
            transformed_command = self.transform_path_placeholders(server.command)
            transformed_command = self.transform_env_placeholders(transformed_command)

            transformed_args = [
                self.transform_env_placeholders(self.transform_path_placeholders(arg)) for arg in server.args
            ]

            transformed_env = {k: self.transform_env_placeholders(v) for k, v in server.env.items()}

            return MCPServerStdioConfig(
                name=server.name,
                transport=server.transport,
                command=transformed_command,
                args=transformed_args,
                env=transformed_env,
            )
        else:  # MCPServerHttpConfig
            transformed_url = self.transform_path_placeholders(server.url)
            transformed_url = self.transform_env_placeholders(transformed_url)

            transformed_headers = {k: self.transform_env_placeholders(v) for k, v in server.headers.items()}

            return MCPServerHttpConfig(
                name=server.name,
                transport=server.transport,
                url=transformed_url,
                headers=transformed_headers,
            )
