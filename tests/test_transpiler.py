"""Tests for core transpiler engine."""

import pytest
from pathlib import Path
import json

from charlie.transpiler import CommandTranspiler
from charlie.parser import ConfigParseError


def create_test_config(tmp_path, config_content: str) -> Path:
    """Helper to create a test configuration file."""
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text(config_content)
    return config_file


def test_transpiler_initialization(tmp_path):
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


def test_transpiler_invalid_config(tmp_path):
    """Test transpiler raises error on invalid config."""
    config_file = create_test_config(tmp_path, "invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError):
        CommandTranspiler(str(config_file))


def test_transpiler_generate_single_agent(tmp_path):
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

    results = transpiler.generate(agents=["claude"], output_dir=str(output_dir))

    assert "claude_commands" in results
    assert len(results["claude_commands"]) == 1

    # Check file was created
    command_file = Path(results["claude_commands"][0])
    assert command_file.exists()
    assert "test.init.md" in str(command_file)


def test_transpiler_generate_multiple_agents(tmp_path):
    """Test generating for multiple agents."""
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

    results = transpiler.generate(
        agents=["claude", "gemini", "cursor"], output_dir=str(output_dir)
    )

    assert "claude_commands" in results
    assert "gemini_commands" in results
    assert "cursor_commands" in results


def test_transpiler_generate_mcp(tmp_path):
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
    with open(mcp_file, "r") as f:
        mcp_config = json.load(f)
    assert "mcpServers" in mcp_config
    assert "test-server" in mcp_config["mcpServers"]


def test_transpiler_generate_rules(tmp_path):
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

    results = transpiler.generate(
        agents=["claude", "windsurf"], rules=True, output_dir=str(output_dir)
    )

    assert "claude_rules" in results
    assert "windsurf_rules" in results

    # Check rules files were created
    claude_rules = Path(results["claude_rules"][0])
    windsurf_rules = Path(results["windsurf_rules"][0])

    assert claude_rules.exists()
    assert windsurf_rules.exists()

    # Check content
    content = claude_rules.read_text()
    assert "# Development Guidelines" in content
    assert "/test.test" in content


def test_transpiler_generate_all(tmp_path):
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

    results = transpiler.generate(
        agents=["claude", "gemini"], mcp=True, rules=True, output_dir=str(output_dir)
    )

    # Check all outputs were generated
    assert "claude_commands" in results
    assert "gemini_commands" in results
    assert "mcp" in results
    assert "claude_rules" in results
    assert "gemini_rules" in results

    # Check command counts
    assert len(results["claude_commands"]) == 2  # init + plan
    assert len(results["gemini_commands"]) == 2


def test_transpiler_generate_mcp_only(tmp_path):
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


def test_transpiler_generate_rules_only(tmp_path):
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

    rules_files = transpiler.generate_rules(["claude", "windsurf"], str(output_dir))

    assert "claude" in rules_files
    assert "windsurf" in rules_files
    assert len(rules_files["claude"]) >= 1
    assert Path(rules_files["claude"][0]).exists()
    assert len(rules_files["windsurf"]) >= 1
    assert Path(rules_files["windsurf"][0]).exists()


def test_transpiler_unknown_agent(tmp_path):
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
        transpiler.generate(agents=["nonexistent"], output_dir="/tmp")


def test_transpiler_creates_nested_directories(tmp_path):
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

    results = transpiler.generate(agents=["claude"], output_dir=str(output_dir))

    # Check that nested directory was created
    assert output_dir.exists()
    command_file = Path(results["claude_commands"][0])
    assert command_file.exists()

