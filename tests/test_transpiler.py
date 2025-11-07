"""Tests for core transpiler engine."""

import json
from pathlib import Path

import pytest

from charlie.parser import ConfigParseError
from charlie.transpiler import CommandTranspiler


def create_test_config(tmp_path, config_content: str) -> Path:
    """Helper to create a test configuration file."""
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text(config_content)
    return config_file


def test_transpiler_initialization(tmp_path) -> None:
    """Test transpiler initializes with valid config."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "init"
    description: "Initialize"
    prompt: "Test prompt"
    scripts:
      sh: "init.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    assert transpiler.config.project.name == "test"
    assert len(transpiler.config.commands) == 1


def test_transpiler_invalid_config(tmp_path) -> None:
    """Test transpiler raises error on invalid config."""
    config_file = create_test_config(tmp_path, "invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError):
        CommandTranspiler(str(config_file))


def test_transpiler_generate_single_agent(tmp_path) -> None:
    """Test generating for a single agent."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "init"
    description: "Initialize"
    prompt: "User: {{user_input}}"
    scripts:
      sh: "init.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    results = transpiler.generate(agent="claude", output_dir=str(output_dir))

    assert "commands" in results
    assert len(results["commands"]) == 1

    # Check file was created
    command_file = Path(results["commands"][0])
    assert command_file.exists()
    assert "test.init.md" in str(command_file)


def test_transpiler_generate_different_agents(tmp_path) -> None:
    """Test generating for different agents separately."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    # Generate for Claude
    results = transpiler.generate(agent="claude", output_dir=str(output_dir))
    assert "commands" in results

    # Generate for Gemini
    results = transpiler.generate(agent="gemini", output_dir=str(output_dir))
    assert "commands" in results

    # Generate for Cursor
    results = transpiler.generate(agent="cursor", output_dir=str(output_dir))
    assert "commands" in results


def test_transpiler_generate_mcp(tmp_path) -> None:
    """Test generating MCP configuration."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
mcp_servers:
  - name: "test-server"
    command: "node"
    args: ["server.js"]
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    results = transpiler.generate(mcp=True, output_dir=str(output_dir))

    assert "mcp" in results
    assert len(results["mcp"]) == 1

    # Check MCP file was created
    mcp_file = Path(results["mcp"][0])
    assert mcp_file.exists()
    assert mcp_file.name == "mcp-config.json"

    # Check content
    with open(mcp_file) as f:
        mcp_config = json.load(f)
    assert "mcpServers" in mcp_config
    assert "test-server" in mcp_config["mcpServers"]


def test_transpiler_generate_rules(tmp_path) -> None:
    """Test generating rules files."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    # Generate for Claude with rules
    results = transpiler.generate(agent="claude", rules=True, output_dir=str(output_dir))

    assert "rules" in results

    # Check rules file was created
    claude_rules = Path(results["rules"][0])
    assert claude_rules.exists()

    # Check content
    content = claude_rules.read_text()
    assert "# Development Guidelines" in content
    assert "/test.test" in content

    # Generate for Windsurf with rules
    results = transpiler.generate(agent="windsurf", rules=True, output_dir=str(output_dir))

    assert "rules" in results
    windsurf_rules = Path(results["rules"][0])
    assert windsurf_rules.exists()


def test_transpiler_generate_all(tmp_path) -> None:
    """Test generating commands, MCP, and rules all at once."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
mcp_servers:
  - name: "test-server"
    command: "node"
    args: ["server.js"]
commands:
  - name: "init"
    description: "Initialize"
    prompt: "Init"
    scripts:
      sh: "init.sh"
  - name: "plan"
    description: "Plan"
    prompt: "Plan"
    scripts:
      sh: "plan.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    # Generate everything for Claude
    results = transpiler.generate(agent="claude", mcp=True, rules=True, output_dir=str(output_dir))

    # Check all outputs were generated
    assert "commands" in results
    assert "mcp" in results
    assert "rules" in results

    # Check command counts
    assert len(results["commands"]) == 2  # init + plan

    # Generate for Gemini
    results = transpiler.generate(agent="gemini", rules=True, output_dir=str(output_dir))

    assert "commands" in results
    assert "rules" in results
    assert len(results["commands"]) == 2


def test_transpiler_generate_mcp_only(tmp_path) -> None:
    """Test generate_mcp method."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
mcp_servers:
  - name: "test-server"
    command: "node"
    args: ["server.js"]
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    mcp_file = transpiler.generate_mcp(str(output_dir))

    assert Path(mcp_file).exists()


def test_transpiler_generate_rules_only(tmp_path) -> None:
    """Test generate_rules method."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "output"

    # Generate rules for Claude
    rules_files = transpiler.generate_rules("claude", str(output_dir))

    assert isinstance(rules_files, list)
    assert len(rules_files) >= 1
    assert Path(rules_files[0]).exists()

    # Generate rules for Windsurf
    rules_files = transpiler.generate_rules("windsurf", str(output_dir))

    assert isinstance(rules_files, list)
    assert len(rules_files) >= 1
    assert Path(rules_files[0]).exists()


def test_transpiler_unknown_agent(tmp_path) -> None:
    """Test that unknown agent raises ValueError."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))

    with pytest.raises(ValueError, match="Unknown agent"):
        transpiler.generate(agent="nonexistent", output_dir="/tmp")


def test_transpiler_creates_nested_directories(tmp_path) -> None:
    """Test that transpiler creates nested output directories."""
    config_file = create_test_config(
        tmp_path,
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test"
    scripts:
      sh: "test.sh"
""",
    )

    transpiler = CommandTranspiler(str(config_file))
    output_dir = tmp_path / "nested" / "deep" / "output"

    results = transpiler.generate(agent="claude", output_dir=str(output_dir))

    # Check that nested directory was created
    assert output_dir.exists()
    command_file = Path(results["commands"][0])
    assert command_file.exists()


def test_transpiler_with_dot_charlie_directory(tmp_path) -> None:
    """Test that transpiler works when passed .charlie directory directly.

    Regression test: Ensure commands are generated when .charlie directory
    is passed as config path (as done by CLI auto-detection).
    """
    # Create directory-based config structure
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

    # Create a command file
    (commands_dir / "test.md").write_text(
        """---
name: "test"
description: "Test command"
scripts:
  sh: "test.sh"
---

Test prompt content
"""
    )

    # Initialize transpiler with .charlie directory path (as CLI does)
    transpiler = CommandTranspiler(str(charlie_dir))

    # Verify config was loaded correctly
    assert len(transpiler.config.commands) == 1
    assert transpiler.config.commands[0].name == "test"

    # Verify root_dir is set to parent of .charlie, not .charlie itself
    assert transpiler.root_dir == str(tmp_path.resolve())

    # Generate commands
    output_dir = tmp_path / "output"
    results = transpiler.generate(agent="cursor", output_dir=str(output_dir))

    # Verify command was generated
    assert "commands" in results
    assert len(results["commands"]) == 1

    # Verify file exists
    generated_file = output_dir / ".cursor" / "commands" / "test.md"

    assert generated_file.exists()

    # Verify content was generated
    content = generated_file.read_text()
    assert "Test command" in content
    assert "Test prompt content" in content
