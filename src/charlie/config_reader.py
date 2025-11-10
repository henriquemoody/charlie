from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from charlie.schema import (
    CharlieConfig,
    Command,
    MCPServer,
    ProjectConfig,
    RulesSection,
)

T = TypeVar("T", bound=BaseModel)


class ConfigParseError(Exception):
    pass


def _infer_project_name(base_dir: Path) -> str:
    return base_dir.resolve().name


def _create_default_config(base_dir: Path) -> CharlieConfig:
    inferred_project_name = _infer_project_name(base_dir)
    return CharlieConfig(
        version="1.0",
        project=ProjectConfig(name=inferred_project_name, command_prefix=None),
        commands=[],
        mcp_servers=[],
    )


def _ensure_project_name(config: CharlieConfig, base_dir: Path) -> CharlieConfig:
    if config.project is None:
        inferred_project_name = _infer_project_name(base_dir)
        config.project = ProjectConfig(name=inferred_project_name, command_prefix=None)
    elif config.project.name is None:
        config.project.name = _infer_project_name(base_dir)

    return config


def parse_frontmatter(content: str) -> tuple[dict, str]:
    stripped_content = content.lstrip()

    if not stripped_content.startswith("---"):
        return {}, stripped_content

    try:
        content_parts = stripped_content.split("---", 2)
        if len(content_parts) < 3:
            raise ConfigParseError("Frontmatter closing delimiter '---' not found")

        frontmatter_text = content_parts[1].strip()
        content_body = content_parts[2].lstrip()

        if not frontmatter_text:
            return {}, content_body

        parsed_frontmatter = yaml.safe_load(frontmatter_text)
        if parsed_frontmatter is None:
            parsed_frontmatter = {}

        return parsed_frontmatter, content_body

    except yaml.YAMLError as e:
        raise ConfigParseError(f"Invalid YAML in frontmatter: {e}")
    except Exception as e:
        raise ConfigParseError(f"Error parsing frontmatter: {e}")


def parse_config(config_path: str | Path) -> CharlieConfig:
    resolved_config_path = Path(config_path)

    if resolved_config_path.is_file():
        base_directory = resolved_config_path.parent
    elif resolved_config_path.is_dir():
        if resolved_config_path.name == ".charlie":
            base_directory = resolved_config_path.parent
        else:
            base_directory = resolved_config_path
    elif resolved_config_path.suffix in [".yaml", ".yml"]:
        base_directory = resolved_config_path.parent
    else:
        base_directory = resolved_config_path

    charlie_config_dir = base_directory / ".charlie"
    if charlie_config_dir.exists() and charlie_config_dir.is_dir():
        return load_directory_config(base_directory)

    if resolved_config_path.is_dir():
        return _create_default_config(base_directory)

    if not resolved_config_path.exists():
        return _create_default_config(base_directory)

    try:
        with open(resolved_config_path, encoding="utf-8") as f:
            raw_config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigParseError(f"Invalid YAML syntax: {e}")
    except Exception as e:
        raise ConfigParseError(f"Error reading configuration file: {e}")

    if not raw_config_data:
        return _create_default_config(base_directory)

    try:
        parsed_config = CharlieConfig(**raw_config_data)
        parsed_config = _ensure_project_name(parsed_config, base_directory)
    except ValidationError as e:
        validation_errors = []
        for error in e.errors():
            error_location = " -> ".join(str(x) for x in error["loc"])
            validation_errors.append(f"  {error_location}: {error['msg']}")
        raise ConfigParseError("Configuration validation failed:\n" + "\n".join(validation_errors))

    return parsed_config


def find_config_file(start_dir: str | Path = ".") -> Path | None:
    resolved_start_dir = Path(start_dir).resolve()

    main_config_file = resolved_start_dir / "charlie.yaml"
    if main_config_file.exists():
        return main_config_file

    hidden_config_file = resolved_start_dir / ".charlie.yaml"
    if hidden_config_file.exists():
        return hidden_config_file

    config_directory = resolved_start_dir / ".charlie"
    if config_directory.exists() and config_directory.is_dir():
        return config_directory

    return None


def parse_single_file(file_path: Path, model_class: type[T]) -> T:
    try:
        with open(file_path, encoding="utf-8") as f:
            file_content = f.read()
    except Exception as e:
        raise ConfigParseError(f"Error reading {file_path}: {e}")

    if not file_content.strip():
        raise ConfigParseError(f"File is empty: {file_path}")

    if file_path.suffix == ".md":
        try:
            parsed_frontmatter, content_body = parse_frontmatter(file_content)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error parsing frontmatter in {file_path}: {e}")

        if model_class.__name__ == "Command":
            raw_data = {**parsed_frontmatter, "prompt": content_body.strip()}
        elif model_class.__name__ == "RulesSection":
            raw_data = {**parsed_frontmatter, "content": content_body.strip()}
        else:
            raw_data = parsed_frontmatter
    else:
        try:
            raw_data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML in {file_path}: {e}")

        if not raw_data:
            raise ConfigParseError(f"File is empty: {file_path}")

    try:
        return model_class(**raw_data)
    except ValidationError as e:
        validation_errors = []
        for error in e.errors():
            error_location = " -> ".join(str(x) for x in error["loc"])
            validation_errors.append(f"  {error_location}: {error['msg']}")
        raise ConfigParseError(f"Validation failed for {file_path}:\n" + "\n".join(validation_errors))


def discover_config_files(base_dir: Path) -> dict[str, list[Path]]:
    charlie_config_directory = base_dir / ".charlie"

    discovered_files: dict[str, list[Path]] = {
        "commands": [],
        "rules": [],
        "mcp_servers": [],
    }

    if not charlie_config_directory.exists():
        return discovered_files

    commands_directory = charlie_config_directory / "commands"
    if commands_directory.exists():
        discovered_files["commands"] = sorted(commands_directory.glob("*.md"))

    rules_directory = charlie_config_directory / "rules"
    if rules_directory.exists():
        discovered_files["rules"] = sorted(rules_directory.glob("*.md"))

    mcp_servers_directory = charlie_config_directory / "mcp-servers"
    if mcp_servers_directory.exists():
        discovered_files["mcp_servers"] = sorted(mcp_servers_directory.glob("*.yaml"))

    return discovered_files


def load_directory_config(base_dir: Path) -> CharlieConfig:
    merged_config_data: dict[str, Any] = {
        "version": "1.0",
        "commands": [],
        "mcp_servers": [],
    }

    main_config_file_path = base_dir / "charlie.yaml"
    if main_config_file_path.exists():
        try:
            with open(main_config_file_path, encoding="utf-8") as f:
                main_config_content = yaml.safe_load(f)
                if main_config_content:
                    if "project" in main_config_content:
                        merged_config_data["project"] = main_config_content["project"]
                    if "version" in main_config_content:
                        merged_config_data["version"] = main_config_content["version"]
        except Exception as e:
            raise ConfigParseError(f"Error reading {main_config_file_path}: {e}")

    discovered_config_files = discover_config_files(base_dir)

    for command_file_path in discovered_config_files["commands"]:
        try:
            parsed_command = parse_single_file(command_file_path, Command)
            if not parsed_command.name:
                parsed_command.name = command_file_path.stem
            merged_config_data["commands"].append(parsed_command.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading command from {command_file_path}: {e}")

    parsed_rules_sections = []
    for rules_file_path in discovered_config_files["rules"]:
        try:
            rules_section = parse_single_file(rules_file_path, RulesSection)
            # Preserve the original filename
            if not rules_section.filename:
                rules_section.filename = rules_file_path.name
            parsed_rules_sections.append(rules_section)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading rule from {rules_file_path}: {e}")

    if parsed_rules_sections:
        # For backward compatibility, store sections in metadata and create a prompt from all sections
        all_content = []
        for section in parsed_rules_sections:
            all_content.append(f"## {section.title}\n\n{section.content}")
        
        merged_config_data["rules"] = {
            "prompt": "\n\n".join(all_content),
            "metadata": {"sections": [s.model_dump() for s in parsed_rules_sections]},
            "replacements": {}
        }

    for mcp_server_file_path in discovered_config_files["mcp_servers"]:
        try:
            mcp_server_config = parse_single_file(mcp_server_file_path, MCPServer)
            merged_config_data["mcp_servers"].append(mcp_server_config.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading MCP server from {mcp_server_file_path}: {e}")

    try:
        final_config = CharlieConfig(**merged_config_data)
        final_config = _ensure_project_name(final_config, base_dir)
        return final_config
    except ValidationError as e:
        validation_errors = []
        for error in e.errors():
            error_location = " -> ".join(str(x) for x in error["loc"])
            validation_errors.append(f"  {error_location}: {error['msg']}")
        raise ConfigParseError("Configuration validation failed:\n" + "\n".join(validation_errors))
