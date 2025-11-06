"""YAML parser with validation."""

from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from charlie.schema import (
    CharlieConfig,
    Command,
    MCPServer,
    RulesSection,
)

T = TypeVar("T", bound=BaseModel)


class ConfigParseError(Exception):
    """Error parsing configuration file."""

    pass


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content.

    Extracts YAML frontmatter between --- delimiters and returns
    both the parsed frontmatter and the remaining content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter_dict, content_body)
        If no frontmatter, returns ({}, original_content)

    Raises:
        ConfigParseError: If frontmatter YAML is invalid
    """
    content = content.lstrip()

    # Check if content starts with frontmatter delimiter
    if not content.startswith("---"):
        return {}, content

    # Find the closing delimiter
    try:
        # Split on --- but skip the first empty match
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ConfigParseError("Frontmatter closing delimiter '---' not found")

        frontmatter_str = parts[1].strip()
        body = parts[2].lstrip()

        # Parse YAML frontmatter
        if not frontmatter_str:
            return {}, body

        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}

        return frontmatter, body

    except yaml.YAMLError as e:
        raise ConfigParseError(f"Invalid YAML in frontmatter: {e}")
    except Exception as e:
        raise ConfigParseError(f"Error parsing frontmatter: {e}")


def parse_config(config_path: str | Path) -> CharlieConfig:
    """Parse and validate a charlie configuration file.

    Automatically detects format:
    - If .charlie/ directory exists: load from directory-based structure
    - Otherwise: load from monolithic charlie.yaml file

    Args:
        config_path: Path to the YAML configuration file or base directory

    Returns:
        Validated CharlieConfig object

    Raises:
        ConfigParseError: If file cannot be read or validation fails
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_path)

    # Determine base directory
    if config_path.is_file():
        base_dir = config_path.parent
    else:
        base_dir = config_path

    # Check if directory-based structure exists
    charlie_dir = base_dir / ".charlie"
    if charlie_dir.exists() and charlie_dir.is_dir():
        # Use directory-based loading
        return load_directory_config(base_dir)

    # Fall back to monolithic file loading
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigParseError(f"Invalid YAML syntax: {e}")
    except Exception as e:
        raise ConfigParseError(f"Error reading configuration file: {e}")

    if not raw_config:
        raise ConfigParseError("Configuration file is empty")

    try:
        config = CharlieConfig(**raw_config)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            error_messages.append(f"  {loc}: {error['msg']}")
        raise ConfigParseError(
            "Configuration validation failed:\n" + "\n".join(error_messages)
        )

    return config


def find_config_file(start_dir: str | Path = ".") -> Path:
    """Find charlie configuration file in order of preference.

    Resolution order:
    1. charlie.yaml in current directory
    2. .charlie.yaml in current directory

    Args:
        start_dir: Directory to search from (default: current directory)

    Returns:
        Path to configuration file

    Raises:
        FileNotFoundError: If no configuration file is found
    """
    start_dir = Path(start_dir).resolve()

    # Check for charlie.yaml
    charlie_yaml = start_dir / "charlie.yaml"
    if charlie_yaml.exists():
        return charlie_yaml

    # Check for .charlie.yaml (hidden)
    hidden_charlie = start_dir / ".charlie.yaml"
    if hidden_charlie.exists():
        return hidden_charlie

    raise FileNotFoundError(
        "No configuration file found. Expected charlie.yaml or .charlie.yaml "
        f"in {start_dir}"
    )


def parse_single_file(file_path: Path, model_class: type[T]) -> T:
    """Parse a single file (YAML or Markdown with frontmatter) into a Pydantic model.

    Args:
        file_path: Path to file (YAML or Markdown)
        model_class: Pydantic model class to parse into

    Returns:
        Instance of model_class

    Raises:
        ConfigParseError: If parsing or validation fails
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            file_content = f.read()
    except Exception as e:
        raise ConfigParseError(f"Error reading {file_path}: {e}")

    if not file_content.strip():
        raise ConfigParseError(f"File is empty: {file_path}")

    # Determine file type and parse accordingly
    if file_path.suffix == ".md":
        # Parse markdown with frontmatter
        try:
            frontmatter, body = parse_frontmatter(file_content)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error parsing frontmatter in {file_path}: {e}")

        # Merge frontmatter and body based on model type
        if model_class.__name__ == "Command":
            # For commands: frontmatter = metadata, body = prompt
            raw_data = {**frontmatter, "prompt": body.strip()}
        elif model_class.__name__ == "RulesSection":
            # For rules: frontmatter = metadata (title, order, etc.), body = content
            raw_data = {**frontmatter, "content": body.strip()}
        else:
            # Generic: just use frontmatter
            raw_data = frontmatter
    else:
        # Parse YAML file
        try:
            raw_data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML in {file_path}: {e}")

        if not raw_data:
            raise ConfigParseError(f"File is empty: {file_path}")

    try:
        return model_class(**raw_data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            error_messages.append(f"  {loc}: {error['msg']}")
        raise ConfigParseError(
            f"Validation failed for {file_path}:\n" + "\n".join(error_messages)
        )


def discover_config_files(base_dir: Path) -> dict[str, list[Path]]:
    """Discover config files in .charlie/ directory structure.

    Args:
        base_dir: Base directory to search from

    Returns:
        Dictionary mapping config type to list of paths:
        {
            "commands": [Path, ...],
            "rules": [Path, ...],
            "mcp_servers": [Path, ...]
        }
    """
    charlie_dir = base_dir / ".charlie"

    result = {
        "commands": [],
        "rules": [],
        "mcp_servers": [],
    }

    if not charlie_dir.exists():
        return result

    # Discover commands (markdown files with frontmatter)
    commands_dir = charlie_dir / "commands"
    if commands_dir.exists():
        result["commands"] = sorted(commands_dir.glob("*.md"))

    # Discover rules (markdown files with frontmatter)
    rules_dir = charlie_dir / "rules"
    if rules_dir.exists():
        result["rules"] = sorted(rules_dir.glob("*.md"))

    # Discover MCP servers (still YAML)
    mcp_dir = charlie_dir / "mcp-servers"
    if mcp_dir.exists():
        result["mcp_servers"] = sorted(mcp_dir.glob("*.yaml"))

    return result


def load_directory_config(base_dir: Path) -> CharlieConfig:
    """Load configuration from directory-based structure.

    Loads from:
    - charlie.yaml (optional project config)
    - .charlie/commands/*.yaml
    - .charlie/rules/*.yaml
    - .charlie/mcp-servers/*.yaml

    Args:
        base_dir: Base directory containing .charlie/

    Returns:
        Merged CharlieConfig

    Raises:
        ConfigParseError: If loading or merging fails
    """
    # Start with minimal config
    config_data = {
        "version": "1.0",
        "commands": [],
        "mcp_servers": [],
    }

    # Try to load main charlie.yaml for project config
    main_config_path = base_dir / "charlie.yaml"
    if main_config_path.exists():
        try:
            with open(main_config_path, encoding="utf-8") as f:
                main_data = yaml.safe_load(f)
                if main_data:
                    # Extract project config if present
                    if "project" in main_data:
                        config_data["project"] = main_data["project"]
                    if "version" in main_data:
                        config_data["version"] = main_data["version"]
        except Exception as e:
            raise ConfigParseError(f"Error reading {main_config_path}: {e}")

    # Discover all config files
    discovered = discover_config_files(base_dir)

    # Load commands
    for command_file in discovered["commands"]:
        try:
            command = parse_single_file(command_file, Command)
            config_data["commands"].append(command.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading command from {command_file}: {e}")

    # Load rules
    rules_sections = []
    for rules_file in discovered["rules"]:
        try:
            section = parse_single_file(rules_file, RulesSection)
            rules_sections.append(section)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading rule from {rules_file}: {e}")

    if rules_sections:
        config_data["rules"] = {
            "sections": [s.model_dump() for s in rules_sections]
        }

    # Load MCP servers
    for mcp_file in discovered["mcp_servers"]:
        try:
            server = parse_single_file(mcp_file, MCPServer)
            config_data["mcp_servers"].append(server.model_dump())
        except ConfigParseError as e:
            raise ConfigParseError(f"Error loading MCP server from {mcp_file}: {e}")

    # Create final config
    try:
        return CharlieConfig(**config_data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            error_messages.append(f"  {loc}: {error['msg']}")
        raise ConfigParseError(
            "Configuration validation failed:\n" + "\n".join(error_messages)
        )

