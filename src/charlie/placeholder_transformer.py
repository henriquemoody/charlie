import os
import re
from typing import Any, final

from charlie.schema import (
    Agent,
    Command,
    HttpMCPServer,
    MCPServer,
    Project,
    ReplacementSpec,
    Rule,
    StdioMCPServer,
)


class EnvironmentVariableNotFoundError(Exception):
    pass


class VariableNotFoundError(Exception):
    pass


class ChoiceNotFoundError(Exception):
    pass


@final
class PlaceholderTransformer:
    def __init__(
        self,
        agent: Agent,
        variables: dict[str, str],
        project: Project,
    ):
        self.agent = agent
        self.variables = variables
        self.project = project

    def command(self, command: Command) -> Command:
        prompt = self.__fixed(command.prompt)
        prompt = self.__replacements(prompt, command.replacements)

        metadata = self.__dict(command.metadata, command.replacements)

        return Command(
            name=command.name,
            description=command.description,
            prompt=prompt,
            metadata=metadata,
            replacements=command.replacements,
        )

    def rule(self, rule: Rule) -> Rule:
        title = self.__fixed(rule.description)
        title = self.__replacements(title, rule.replacements)

        prompt = self.__fixed(rule.prompt)
        prompt = self.__replacements(prompt, rule.replacements)

        metadata = self.__dict(rule.metadata, rule.replacements)

        return Rule(
            name=rule.name,
            description=title,
            prompt=prompt,
            metadata=metadata,
            replacements=rule.replacements,
        )

    def mcp_server(self, mcp_server: MCPServer) -> MCPServer:
        if isinstance(mcp_server, HttpMCPServer):
            return HttpMCPServer(
                name=mcp_server.name,
                type=mcp_server.type,
                url=self.__fixed(mcp_server.url),
                headers={k: self.__fixed(v) for k, v in mcp_server.headers.items()},
            )

        return StdioMCPServer(
            name=mcp_server.name,
            type=mcp_server.type,
            command=self.__fixed(mcp_server.command),
            args=[self.__fixed(arg) for arg in mcp_server.args],
            env={variable: self.__fixed(value) for variable, value in mcp_server.env.items()},
        )

    def __fixed(self, text: str) -> str:
        text = self.__static(text)
        text = self.__var(text)
        text = self.__env(text)

        return text

    def __static(self, text: str) -> str:
        # Use relative paths if project_dir is the current working directory
        cwd = os.path.abspath(os.getcwd())
        project_dir_abs = os.path.abspath(self.project.dir)
        use_relative = cwd == project_dir_abs

        placeholders = {
            "{{project_dir}}": ".",
            "{{project_name}}": self.project.name,
            "{{project_namespace}}": self.project.namespace or "",
            "{{agent_name}}": self.agent.name,
            "{{agent_shortname}}": self.agent.shortname,
            "{{agent_dir}}": self.agent.dir,
            "{{commands_dir}}": self.agent.commands_dir,
            "{{commands_shorthand_injection}}": self.agent.commands_shorthand_injection,
            "{{rules_dir}}": self.agent.rules_dir,
            "{{rules_file}}": self.agent.rules_file,
            "{{mcp_file}}": self.agent.mcp_file,
            "{{assets_dir}}": self.agent.dir + "/assets",
        }

        if not use_relative:
            for placeholder, replacement in placeholders.items():
                if placeholder.endswith("_dir}}") or placeholder.endswith("_file}}"):
                    placeholders[placeholder] = self.project.dir + "/" + replacement
            placeholders["{{project_dir}}"] = self.project.dir

        for placeholder, replacement in placeholders.items():
            text = text.replace(placeholder, replacement)

        return text

    def __var(self, text: str) -> str:
        for variable_name, variable_value in self.variables.items():
            text = text.replace("{{var:" + variable_name + "}}", variable_value)

        return text

    def __env(self, text: str) -> str:
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

    def __replacements(self, text: str, replacements: dict[str, ReplacementSpec]) -> str:
        for placeholder, spect in replacements.items():
            placeholder = "{{" + placeholder + "}}"
            if spect.type == "value":
                text = text.replace(placeholder, str(spect.value))
                continue

            variable = self.variables.get(spect.discriminator)
            if variable is None:
                raise VariableNotFoundError(f"Variable not found: {spect.discriminator}")

            choice = spect.options.get(variable)
            if choice is None:
                raise ChoiceNotFoundError(f"Choice not found for variable: {variable}")

            text = text.replace(placeholder, choice)

        return text

    def __dict(self, original: dict[str, Any], replacements: dict[str, ReplacementSpec]) -> dict[str, Any]:
        transformed: dict[str, Any] = {}
        for key, value in original.items():
            if isinstance(value, str):
                transformed_value = self.__fixed(value)
                transformed_value = self.__replacements(transformed_value, replacements)
                transformed[key] = transformed_value
            elif isinstance(value, dict):
                transformed[key] = self.__dict(value, replacements)
            elif isinstance(value, list):
                transformed[key] = self.__list(value, replacements)
            else:
                transformed[key] = value

        return transformed

    def __list(self, original: list[Any], replacements: dict[str, ReplacementSpec]) -> list[Any]:
        transformed: list[Any] = []
        for item in original:
            if isinstance(item, str):
                transformed_value = self.__fixed(item)
                transformed_value = self.__replacements(transformed_value, replacements)
                transformed.append(transformed_value)
            elif isinstance(item, dict):
                transformed.append(self.__dict(item, replacements))
            elif isinstance(item, list):
                transformed.append(self.__list(item, replacements))
            else:
                transformed.append(item)

        return transformed
