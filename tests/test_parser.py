"""Tests for parser module."""

import pytest
from pathlib import Path
import tempfile
import os

from charlie.parser import (
    parse_config,
    find_config_file,
    parse_single_file,
    discover_config_files,
    load_directory_config,
    ConfigParseError,
)
from charlie.schema import Command, RulesSection, MCPServer


def test_parse_valid_config(tmp_path):
    """Test parsing a valid configuration file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test-project"
  command_prefix: "test"
commands:
  - name: "init"
    description: "Initialize"
    prompt: "Test prompt"
    scripts:
      sh: "init.sh"
"""
    )

    config = parse_config(config_file)
    assert config.version == "1.0"
    assert config.project.name == "test-project"
    assert len(config.commands) == 1


def test_parse_nonexistent_file():
    """Test parsing a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_config("/nonexistent/config.yaml")


def test_parse_empty_file(tmp_path):
    """Test parsing an empty file raises ConfigParseError."""
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")

    with pytest.raises(ConfigParseError, match="empty"):
        parse_config(config_file)


def test_parse_invalid_yaml(tmp_path):
    """Test parsing invalid YAML raises ConfigParseError."""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError, match="Invalid YAML syntax"):
        parse_config(config_file)


def test_parse_invalid_schema(tmp_path):
    """Test parsing YAML with invalid schema raises ConfigParseError."""
    config_file = tmp_path / "invalid_schema.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test"
# Missing command_prefix and commands
"""
    )

    with pytest.raises(ConfigParseError, match="validation failed"):
        parse_config(config_file)


def test_find_config_charlie_yaml(tmp_path):
    """Test finding charlie.yaml file."""
    config_file = tmp_path / "charlie.yaml"
    config_file.write_text("test")

    found = find_config_file(tmp_path)
    assert found == config_file


def test_find_config_hidden_charlie(tmp_path):
    """Test finding .charlie.yaml file."""
    config_file = tmp_path / ".charlie.yaml"
    config_file.write_text("test")

    found = find_config_file(tmp_path)
    assert found == config_file


def test_find_config_prefers_non_hidden(tmp_path):
    """Test that charlie.yaml is preferred over .charlie.yaml."""
    visible = tmp_path / "charlie.yaml"
    hidden = tmp_path / ".charlie.yaml"
    visible.write_text("visible")
    hidden.write_text("hidden")

    found = find_config_file(tmp_path)
    assert found == visible


def test_find_config_not_found(tmp_path):
    """Test that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="No configuration file found"):
        find_config_file(tmp_path)


def test_parse_config_with_mcp_servers(tmp_path):
    """Test parsing configuration with MCP servers."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
mcp_servers:
  - name: "server1"
    command: "node"
    args: ["server.js"]
    env:
      DEBUG: "true"
commands:
  - name: "test"
    description: "Test"
    prompt: "Prompt"
    scripts:
      sh: "test.sh"
"""
    )

    config = parse_config(config_file)
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "server1"
    assert config.mcp_servers[0].env["DEBUG"] == "true"


def test_parse_single_file_command(tmp_path):
    """Test parsing a single command file."""
    command_file = tmp_path / "init.yaml"
    command_file.write_text(
        """
name: "init"
description: "Initialize project"
prompt: "Initialize with {{user_input}}"
scripts:
  sh: "init.sh"
  ps: "init.ps1"
"""
    )

    command = parse_single_file(command_file, Command)
    assert command.name == "init"
    assert command.description == "Initialize project"
    assert command.scripts.sh == "init.sh"


def test_parse_single_file_rules_section(tmp_path):
    """Test parsing a single rules section file."""
    rules_file = tmp_path / "code-style.yaml"
    rules_file.write_text(
        """
title: "Code Style"
content: |
  Use Black for formatting
  Max line length: 100
order: 1
alwaysApply: true
globs:
  - "**/*.py"
"""
    )

    section = parse_single_file(rules_file, RulesSection)
    assert section.title == "Code Style"
    assert "Black" in section.content
    assert section.order == 1
    # Verify pass-through fields
    section_dict = section.model_dump()
    assert section_dict["alwaysApply"] is True
    assert section_dict["globs"] == ["**/*.py"]


def test_parse_single_file_invalid(tmp_path):
    """Test parsing invalid file raises ConfigParseError."""
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("name: test\n# missing required fields")

    with pytest.raises(ConfigParseError, match="Validation failed"):
        parse_single_file(invalid_file, Command)


def test_discover_config_files_empty(tmp_path):
    """Test discovering config files when .charlie/ doesn't exist."""
    result = discover_config_files(tmp_path)
    assert result["commands"] == []
    assert result["rules"] == []
    assert result["mcp_servers"] == []


def test_discover_config_files_complete(tmp_path):
    """Test discovering config files in complete directory structure."""
    # Create directory structure
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    rules_dir = charlie_dir / "rules"
    mcp_dir = charlie_dir / "mcp-servers"

    commands_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    mcp_dir.mkdir(parents=True)

    # Create files
    (commands_dir / "init.yaml").write_text("test")
    (commands_dir / "build.yaml").write_text("test")
    (rules_dir / "style.yaml").write_text("test")
    (mcp_dir / "server.yaml").write_text("test")

    result = discover_config_files(tmp_path)
    assert len(result["commands"]) == 2
    assert len(result["rules"]) == 1
    assert len(result["mcp_servers"]) == 1


def test_load_directory_config_minimal(tmp_path):
    """Test loading minimal directory-based config."""
    # Create structure
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

    # Create one command
    (commands_dir / "test.yaml").write_text(
        """
name: "test"
description: "Test command"
prompt: "Test"
scripts:
  sh: "test.sh"
"""
    )

    config = load_directory_config(tmp_path)
    assert config.version == "1.0"
    assert config.project is None  # No project config
    assert len(config.commands) == 1
    assert config.commands[0].name == "test"


def test_load_directory_config_with_project(tmp_path):
    """Test loading directory config with project metadata."""
    # Create charlie.yaml with project info
    (tmp_path / "charlie.yaml").write_text(
        """
version: "1.0"
project:
  name: "my-project"
  command_prefix: "myapp"
"""
    )

    # Create command
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "init.yaml").write_text(
        """
name: "init"
description: "Init"
prompt: "Init"
scripts:
  sh: "init.sh"
"""
    )

    config = load_directory_config(tmp_path)
    assert config.project is not None
    assert config.project.name == "my-project"
    assert config.project.command_prefix == "myapp"
    assert len(config.commands) == 1


def test_load_directory_config_with_rules(tmp_path):
    """Test loading directory config with rules sections."""
    # Create rules
    charlie_dir = tmp_path / ".charlie"
    rules_dir = charlie_dir / "rules"
    commands_dir = charlie_dir / "commands"
    rules_dir.mkdir(parents=True)
    commands_dir.mkdir(parents=True)

    (rules_dir / "style.yaml").write_text(
        """
title: "Code Style"
content: "Use Black"
order: 1
"""
    )

    (rules_dir / "commits.yaml").write_text(
        """
title: "Commit Messages"
content: "Use conventional commits"
order: 2
"""
    )

    # Need at least one command for valid config
    (commands_dir / "test.yaml").write_text(
        """
name: "test"
description: "Test"
prompt: "Test"
scripts:
  sh: "test.sh"
"""
    )

    config = load_directory_config(tmp_path)
    assert config.rules is not None
    assert config.rules.sections is not None
    assert len(config.rules.sections) == 2
    # Check both sections exist (order not guaranteed in loading)
    titles = [s.title for s in config.rules.sections]
    assert "Code Style" in titles
    assert "Commit Messages" in titles


def test_load_directory_config_with_mcp(tmp_path):
    """Test loading directory config with MCP servers."""
    charlie_dir = tmp_path / ".charlie"
    mcp_dir = charlie_dir / "mcp-servers"
    commands_dir = charlie_dir / "commands"
    mcp_dir.mkdir(parents=True)
    commands_dir.mkdir(parents=True)

    (mcp_dir / "local.yaml").write_text(
        """
name: "local-tools"
command: "node"
args: ["server.js"]
commands: ["init", "build"]
"""
    )

    # Need at least one command
    (commands_dir / "init.yaml").write_text(
        """
name: "init"
description: "Init"
prompt: "Init"
scripts:
  sh: "init.sh"
"""
    )

    config = load_directory_config(tmp_path)
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "local-tools"
    assert config.mcp_servers[0].commands == ["init", "build"]


def test_parse_config_detects_directory_format(tmp_path):
    """Test that parse_config detects directory-based format."""
    # Create directory structure
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

    (commands_dir / "test.yaml").write_text(
        """
name: "test"
description: "Test"
prompt: "Test"
scripts:
  sh: "test.sh"
"""
    )

    # Also create a charlie.yaml that would be invalid if used
    (tmp_path / "charlie.yaml").write_text(
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
"""
    )

    # parse_config should use directory loading
    config = parse_config(tmp_path / "charlie.yaml")
    assert len(config.commands) == 1  # From directory, not from file
    assert config.commands[0].name == "test"


def test_parse_config_fallback_to_monolithic(tmp_path):
    """Test that parse_config falls back to monolithic when no .charlie/ exists."""
    config_file = tmp_path / "charlie.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "init"
    description: "Init"
    prompt: "Init"
    scripts:
      sh: "init.sh"
"""
    )

    config = parse_config(config_file)
    assert config.project.name == "test"
    assert len(config.commands) == 1

