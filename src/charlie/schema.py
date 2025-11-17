from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from charlie.enums import FileFormat, TransportType


class Agent(BaseModel):
    name: str = Field(..., description="Name of the agent")
    shortname: str = Field(..., description="Short version of the agent name")
    dir: str = Field(..., description="Root directory of the agent")
    default_format: FileFormat = Field(..., description="Default file format")
    commands_dir: str = Field(..., description="Directory containing command files")
    commands_extension: str = Field(..., description="Extension of command files")
    commands_shorthand_injection: str = Field(..., description="Placeholder for shorthand injection in command files")
    rules_dir: str = Field(..., description="Directory where rules are stored")
    rules_file: str = Field(..., description="Default rules file")
    rules_extension: str = Field(..., description="Default extension for rules files")
    mcp_file: str = Field(..., description="MCP file")
    ignore_file: str | None = Field(None, description="Ignore file path (e.g., .cursorignore, .claude/.clignore)")


class Project(BaseModel):
    name: str = Field(..., description="Project name")
    namespace: str | None = Field(None, description="Namespace for commands and rules")
    dir: str = Field(..., description="Project directory")


class VariableSpec(BaseModel):
    env: str | None = Field(None, description="Environment variable name")
    choices: list[str] | None = Field(None, description="Available choices for the variable")
    default: str | None = Field(None, description="Default value")


class StdioMCPServer(BaseModel):
    name: str = Field(..., description="Server name")
    type: TransportType = Field(default=TransportType.STDIO, description="Transport type (stdio)")
    command: str = Field(..., description="Command to run the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class HttpMCPServer(BaseModel):
    """MCP server configuration for HTTP type."""

    name: str = Field(..., description="Server name")
    type: TransportType = Field(default=TransportType.HTTP, description="Transport type (http)")
    url: str = Field(..., description="Server URL")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")


MCPServer = StdioMCPServer | HttpMCPServer

Metadata = dict[str, Any]


class ChoiceReplacement(BaseModel):
    type: Literal["choice"] = Field(default="choice", description="Says that the type is choice")
    discriminator: str = Field(..., description="Discriminator key")
    options: dict[str, str] = Field(..., description="Available options for the variable")


class ValueReplacement(BaseModel):
    type: Literal["value"] = Field(default="value", description="Says that the type is choice")
    value: str | int | float | bool | None = Field(..., description="Value to replace with")


ReplacementSpec = ChoiceReplacement | ValueReplacement


class Rule(BaseModel):
    name: str = Field(..., description="Name of the rule")
    description: str = Field(..., description="Description of the rule")
    prompt: str = Field(default="", description="Rules prompt template")
    metadata: Metadata = Field(default_factory=dict, description="Rules metadata")
    replacements: dict[str, ReplacementSpec] = Field(default_factory=dict, description="String replacements")


class Command(BaseModel):
    name: str = Field(..., description="Command name")
    description: str = Field(..., description="Command description")
    prompt: str = Field(..., description="Command prompt template")
    metadata: Metadata = Field(default_factory=dict, description="Command metadata")
    replacements: dict[str, ReplacementSpec] = Field(default_factory=dict, description="String replacements")


class CharlieConfig(BaseModel):
    version: str = Field("1.0", description="Schema version")
    project: Project = Field(..., description="Project configuration")
    commands: list[Command] = Field(default_factory=list, description="Command definitions")
    rules: list[Rule] = Field(default_factory=list, description="Rules configuration")
    mcp_servers: list[MCPServer] = Field(default_factory=list, description="MCP server definitions")
    variables: dict[str, VariableSpec | None] = Field(default_factory=dict, description="Variable definitions")
    assets: list[str] = Field(default_factory=list, description="List of existing assets")
    ignore_patterns: list[str] = Field(default_factory=list, description="Patterns to add to agent ignore files")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not v.startswith("1."):
            raise ValueError("Only schema version 1.x is supported")
        return v

    @field_validator("commands")
    @classmethod
    def validate_unique_command_names(cls, v: list[Command]) -> list[Command]:
        command_names = [cmd.name for cmd in v]
        if len(command_names) != len(set(command_names)):
            duplicate_names = [name for name in command_names if command_names.count(name) > 1]
            raise ValueError(f"Duplicate command names found: {set(duplicate_names)}")
        return v
