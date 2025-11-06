"""YAML schema definitions and validation using Pydantic."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectConfig(BaseModel):
    """Project metadata configuration."""

    name: str = Field(..., description="Project name")
    command_prefix: str = Field(..., description="Command prefix for slash commands")


class MCPServer(BaseModel):
    """MCP server configuration with pass-through for agent-specific fields."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Server name")
    command: str = Field(..., description="Command to run the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    commands: list[str] | None = Field(
        None, description="Command names this server should expose"
    )
    config: dict[str, Any] | None = Field(
        None, description="Server-specific configuration"
    )


class RulesSection(BaseModel):
    """Individual rules section from a separate file."""

    model_config = ConfigDict(extra="allow")

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content (Markdown)")
    order: int | None = Field(None, description="Display order (lower numbers first)")


class RulesConfig(BaseModel):
    """Rules file configuration."""

    title: str = Field(default="Development Guidelines", description="Rules file title")
    include_commands: bool = Field(default=True, description="Include commands reference")
    include_tech_stack: bool = Field(
        default=True, description="Include technology stack info"
    )
    preserve_manual: bool = Field(
        default=True, description="Preserve manual additions between markers"
    )
    sections: list[RulesSection] | None = Field(
        None, description="Custom rule sections (from directory-based config)"
    )


class CommandScripts(BaseModel):
    """Script definitions for different platforms."""

    sh: str | None = Field(None, description="Bash script path")
    ps: str | None = Field(None, description="PowerShell script path")

    @field_validator("sh", "ps")
    @classmethod
    def validate_at_least_one(cls, v: str | None, info) -> str | None:
        """Ensure at least one script is defined."""
        return v


class Command(BaseModel):
    """Command definition with pass-through for agent-specific fields."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, description="Command name (without prefix)")
    description: str = Field(..., description="Command description")
    prompt: str = Field(default="", description="Command prompt template")
    scripts: CommandScripts | None = Field(None, description="Platform-specific scripts")
    agent_scripts: CommandScripts | None = Field(
        None, description="Optional agent-specific scripts"
    )

    @field_validator("scripts")
    @classmethod
    def validate_scripts(cls, v: CommandScripts | None) -> CommandScripts | None:
        """Ensure at least one script is provided if scripts are defined."""
        if v is not None and not v.sh and not v.ps:
            raise ValueError("At least one script (sh or ps) must be defined")
        return v


class CharlieConfig(BaseModel):
    """Main configuration schema for charlie."""

    version: str = Field(default="1.0", description="Schema version")
    project: ProjectConfig | None = Field(None, description="Project configuration")
    mcp_servers: list[MCPServer] = Field(
        default_factory=list, description="MCP server definitions"
    )
    rules: RulesConfig | None = Field(
        default_factory=RulesConfig, description="Rules configuration"
    )
    commands: list[Command] = Field(default_factory=list, description="Command definitions")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate schema version format."""
        if not v.startswith("1."):
            raise ValueError("Only schema version 1.x is supported")
        return v

    @field_validator("commands")
    @classmethod
    def validate_unique_command_names(cls, v: list[Command]) -> list[Command]:
        """Ensure command names are unique."""
        names = [cmd.name for cmd in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate command names found: {set(duplicates)}")
        return v

