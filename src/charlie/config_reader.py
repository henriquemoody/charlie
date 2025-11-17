from pathlib import Path
from typing import Any, TypeVar, get_origin

import yaml
from pydantic import BaseModel, TypeAdapter, ValidationError
from slugify import slugify

from charlie.schema import (
    CharlieConfig,
    Command,
    MCPServer,
    Project,
    Rule,
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
        project=Project(
            name=inferred_project_name,
            namespace=None,
            dir=".",
        ),
        commands=[],
        mcp_servers=[],
    )


def _ensure_project_name(config: CharlieConfig, base_dir: Path) -> CharlieConfig:
    if config.project is None:
        inferred_project_name = _infer_project_name(base_dir)
        config.project = Project(name=inferred_project_name, namespace=None)
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

    default_project = {"name": base_directory.stem, "dir": str(base_directory)}

    if "project" not in raw_config_data:
        raw_config_data["project"] = default_project

    raw_config_data["project"] = {**default_project, **raw_config_data["project"]}

    # Auto-generate names from descriptions if missing
    for command in raw_config_data.get("commands") or []:
        if "name" not in command and "description" in command:
            command["name"] = slugify(command["description"])

    for rule in raw_config_data.get("rules") or []:
        if "name" not in rule and "description" in rule:
            rule["name"] = slugify(rule["description"])

    raw_config_data["variables"] = raw_config_data.get("variables") or {}

    # Merge ignore patterns from YAML and .charlieignore
    # Always include .charlie directory as the first pattern
    default_patterns = [".charlie"]
    yaml_patterns = raw_config_data.get("ignore_patterns") or []
    file_patterns = read_ignore_patterns(base_directory)

    # Combine all sources: defaults first, then YAML, then file patterns
    # Remove duplicates while preserving order
    all_patterns = default_patterns + yaml_patterns + file_patterns
    seen = set()
    unique_patterns = []
    for pattern in all_patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)

    if unique_patterns:
        raw_config_data["ignore_patterns"] = unique_patterns

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

    dist_config_file = resolved_start_dir / "charlie.dist.yaml"
    if dist_config_file.exists():
        return dist_config_file

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
            name = parsed_frontmatter.get("name")
            if name is None:
                name = slugify(file_path.stem)

            # Separate known Command fields from metadata
            known_fields = {"name", "description", "prompt", "metadata", "replacements"}
            metadata = {k: v for k, v in parsed_frontmatter.items() if k not in known_fields}

            raw_data = {
                "name": name,
                "description": parsed_frontmatter.get("description", ""),
                "prompt": content_body.strip(),
                "metadata": {**parsed_frontmatter.get("metadata", {}), **metadata},
            }

            # Include replacements if present
            if "replacements" in parsed_frontmatter:
                raw_data["replacements"] = parsed_frontmatter["replacements"]

        elif model_class.__name__ == "Rule":
            name = parsed_frontmatter.get("name")
            if name is None:
                name = slugify(file_path.stem)

            # Separate known Rule fields from metadata
            known_fields = {"name", "description", "prompt", "metadata", "replacements"}
            metadata = {k: v for k, v in parsed_frontmatter.items() if k not in known_fields}

            raw_data = {
                "name": name,
                "description": parsed_frontmatter.get("description", ""),
                "prompt": content_body.strip(),
                "metadata": {**parsed_frontmatter.get("metadata", {}), **metadata},
            }

            # Include replacements if present
            if "replacements" in parsed_frontmatter:
                raw_data["replacements"] = parsed_frontmatter["replacements"]
        else:
            raw_data = parsed_frontmatter
    else:
        try:
            raw_data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML in {file_path}: {e}")

        if not raw_data:
            raise ConfigParseError(f"File is empty: {file_path}")

        if str(model_class).find("MCPServer") != -1:
            if "name" not in raw_data:
                raw_data["name"] = slugify(file_path.stem)

    try:
        # Check if model_class is a union type
        if get_origin(model_class) is None:
            return model_class(**raw_data)

        adapter = TypeAdapter(model_class)

        return adapter.validate_python(raw_data)
    except ValidationError as e:
        validation_errors = []
        for error in e.errors():
            error_location = " -> ".join(str(x) for x in error["loc"])
            validation_errors.append(f"  {error_location}: {error['msg']}")
        raise ConfigParseError(f"Validation failed for {file_path}:\n" + "\n".join(validation_errors))


def discover_charlie_files(base_dir: Path) -> dict[str, list[Path]]:
    charlie_config_directory = base_dir / ".charlie"

    discovered_files: dict[str, list[Path]] = {
        "commands": [],
        "rules": [],
        "mcp_servers": [],
        "assets": [],
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

    assets_directory = charlie_config_directory / "assets"
    if assets_directory.exists():
        discovered_files["assets"] = sorted(assets_directory.rglob("*.*"))

    return discovered_files


def read_ignore_patterns(base_dir: Path) -> list[str]:
    """Read ignore patterns from .charlieignore file.

    Args:
        base_dir: Base directory to search for .charlieignore file

    Returns:
        List of patterns from .charlieignore file, or empty list if file doesn't exist
    """
    charlieignore_file = base_dir / ".charlieignore"

    if not charlieignore_file.exists():
        return []

    try:
        with open(charlieignore_file, encoding="utf-8") as f:
            lines = f.readlines()

        patterns = []
        for line in lines:
            # Strip whitespace and skip empty lines and comments
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)

        return patterns
    except Exception as e:
        raise ConfigParseError(f"Error reading {charlieignore_file}: {e}")


def load_directory_config(base_dir: Path) -> CharlieConfig:
    default_project = {"name": base_dir.stem, "dir": str(base_dir)}
    merged_config_data: dict[str, Any] = {
        "version": "1.0",
        "project": default_project,
        "commands": [],
        "rules": [],
        "mcp_servers": [],
    }

    main_config_file_path = base_dir / "charlie.yaml"
    main_config_file_path_dist = base_dir / "charlie.dist.yaml"
    if main_config_file_path.exists() or main_config_file_path_dist.exists():
        try:
            chosen_config_file = main_config_file_path if main_config_file_path.exists() else main_config_file_path_dist
            with open(chosen_config_file, encoding="utf-8") as f:
                main_config_content = yaml.safe_load(f)
                if main_config_content:
                    if "project" in main_config_content:
                        merged_config_data["project"] = main_config_content["project"]
                    if "version" in main_config_content:
                        merged_config_data["version"] = main_config_content["version"]
                    if "variables" in main_config_content:
                        merged_config_data["variables"] = main_config_content["variables"]
                    if "ignore_patterns" in main_config_content:
                        merged_config_data["ignore_patterns"] = main_config_content["ignore_patterns"]
        except Exception as e:
            raise ConfigParseError(f"Error reading {chosen_config_file}: {e}")

    discovered_config_files = discover_charlie_files(base_dir)

    for command_file_path in discovered_config_files["commands"]:
        try:
            parsed_command = parse_single_file(command_file_path, Command)
            merged_config_data["commands"].append(parsed_command.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading command from {command_file_path}: {e}")

    for rules_file_path in discovered_config_files["rules"]:
        try:
            parsed_rule = parse_single_file(rules_file_path, Rule)
            if not parsed_rule.name:
                parsed_rule.name = slugify(Path(rules_file_path).stem)
            merged_config_data["rules"].append(parsed_rule)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading rule from {rules_file_path}: {e}")

    for mcp_server_file_path in discovered_config_files["mcp_servers"]:
        try:
            mcp_server_config: MCPServer = parse_single_file(mcp_server_file_path, MCPServer)  # type: ignore[arg-type]
            merged_config_data["mcp_servers"].append(mcp_server_config.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading MCP server from {mcp_server_file_path}: {e}")

    merged_config_data["project"] = {**default_project, **merged_config_data["project"]}
    merged_config_data["assets"] = [str(value) for value in discovered_config_files["assets"]]

    # Merge ignore patterns from .charlieignore with any already in merged_config_data
    # Always include .charlie directory as the first pattern
    default_patterns = [".charlie"]
    yaml_patterns = merged_config_data.get("ignore_patterns") or []
    file_patterns = read_ignore_patterns(base_dir)

    # Combine all sources: defaults first, then YAML, then file patterns
    # Remove duplicates while preserving order
    all_patterns = default_patterns + yaml_patterns + file_patterns
    seen = set()
    unique_patterns = []
    for pattern in all_patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)

    if unique_patterns:
        merged_config_data["ignore_patterns"] = unique_patterns

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
