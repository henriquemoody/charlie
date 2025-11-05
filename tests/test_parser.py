"""Tests for parser module."""

import pytest
from pathlib import Path
import tempfile
import os

from charlie.parser import parse_config, find_config_file, ConfigParseError


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

