"""YAML parser with validation."""

import yaml
from pathlib import Path
from typing import Union
from pydantic import ValidationError

from charlie.schema import CharlieConfig


class ConfigParseError(Exception):
    """Error parsing configuration file."""

    pass


def parse_config(config_path: Union[str, Path]) -> CharlieConfig:
    """Parse and validate a charlie configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Validated CharlieConfig object

    Raises:
        ConfigParseError: If file cannot be read or validation fails
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
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
            f"Configuration validation failed:\n" + "\n".join(error_messages)
        )

    return config


def find_config_file(start_dir: Union[str, Path] = ".") -> Path:
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

