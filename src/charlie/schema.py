from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class AgentSpec(BaseModel):
    name: str
    command_dir: str
    rules_file: str
    rules_dir: str
    file_format: str
    command_extension: str
    rules_extension: str
    arg_placeholder: str
    mcp_config_path: str


class ProjectConfig(BaseModel):
    name: str | None = Field(None, description="Project name (inferred from directory if not specified)")
    command_prefix: str | None = Field(None, description="Command prefix for slash commands")


class MCPServer(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Server name")
    command: str = Field(..., description="Command to run the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    commands: list[str] | None = Field(None, description="Command names this server should expose")
    config: dict[str, Any] | None = Field(None, description="Server-specific configuration")


class RulesSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content (Markdown)")
    order: int | None = Field(None, description="Display order (lower numbers first)")
    filename: str | None = Field(None, description="Original filename (for directory-based configs)")


class RulesConfig(BaseModel):
    title: str = Field(default="Development Guidelines", description="Rules file title")
    include_commands: bool = Field(default=True, description="Include commands reference")
    include_tech_stack: bool = Field(default=True, description="Include technology stack info")
    preserve_manual: bool = Field(default=True, description="Preserve manual additions between markers")
    sections: list[RulesSection] | None = Field(None, description="Custom rule sections (from directory-based config)")


class CommandScripts(BaseModel):
    sh: str | None = Field(None, description="Bash script path")
    ps: str | None = Field(None, description="PowerShell script path")

    @field_validator("sh", "ps")
    @classmethod
    def validate_at_least_one(cls, v: str | None, info: ValidationInfo) -> str | None:
        return v


class Command(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, description="Command name (without prefix)")
    description: str = Field(..., description="Command description")
    prompt: str = Field(default="", description="Command prompt template")
    scripts: CommandScripts | None = Field(None, description="Platform-specific scripts")
    agent_scripts: CommandScripts | None = Field(None, description="Optional agent-specific scripts")

    @field_validator("scripts")
    @classmethod
    def validate_scripts(cls, v: CommandScripts | None) -> CommandScripts | None:
        if v is not None and not v.sh and not v.ps:
            raise ValueError("At least one script (sh or ps) must be defined")
        return v


class CharlieConfig(BaseModel):
    version: str = Field(default="1.0", description="Schema version")
    project: ProjectConfig | None = Field(None, description="Project configuration")
    mcp_servers: list[MCPServer] = Field(default_factory=list, description="MCP server definitions")
    rules: RulesConfig | None = Field(default=None, description="Rules configuration")
    commands: list[Command] = Field(default_factory=list, description="Command definitions")

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
