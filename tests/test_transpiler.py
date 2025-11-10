import json
from pathlib import Path

import pytest

from charlie.config_reader import ConfigParseError
from charlie.transpiler import CommandTranspiler


def create_test_config(tmp_path, config_content: str) -> Path:
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text(config_content)
    return config_file


def test_transpiler_initialization_with_valid_config(tmp_path) -> None:
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


def test_transpiler_invalid_config_raises_error(tmp_path) -> None:
    config_file = create_test_config(tmp_path, "invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError):
        CommandTranspiler(str(config_file))


def test_transpiler_generate_single_agent_creates_command_file(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", output_dir=str(output_dir))

    assert "commands" in results
    assert len(results["commands"]) == 1

    command_file = Path(results["commands"][0])
    assert command_file.exists()
    assert "test.init.md" in str(command_file)


def test_transpiler_generate_different_agents_separately(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", output_dir=str(output_dir))
    assert "commands" in results

    results = transpiler.generate(agent_name="gemini", output_dir=str(output_dir))
    assert "commands" in results

    results = transpiler.generate(agent_name="cursor", output_dir=str(output_dir))
    assert "commands" in results


def test_transpiler_generate_mcp_configuration(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="opencode", mcp=True, output_dir=str(output_dir))

    assert "mcp" in results
    assert len(results["mcp"]) == 1

    mcp_file = Path(results["mcp"][0])
    assert mcp_file.exists()
    assert mcp_file.name == "mcp-config.json"

    with open(mcp_file) as f:
        mcp_config = json.load(f)
    assert "mcpServers" in mcp_config
    assert "test-server" in mcp_config["mcpServers"]


def test_transpiler_generate_rules_files_for_multiple_agents(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", rules=True, output_dir=str(output_dir))

    assert "rules" in results

    claude_rules = Path(results["rules"][0])
    assert claude_rules.exists()

    content = claude_rules.read_text()
    assert "# Development Guidelines" in content
    assert "/test.test" in content

    results = transpiler.generate(agent_name="windsurf", rules=True, output_dir=str(output_dir))

    assert "rules" in results
    windsurf_rules = Path(results["rules"][0])
    assert windsurf_rules.exists()


def test_transpiler_generate_commands_mcp_and_rules_all_at_once(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", mcp=True, rules=True, output_dir=str(output_dir))

    assert "commands" in results
    assert "mcp" in results
    assert "rules" in results

    assert len(results["commands"]) == 2

    results = transpiler.generate(agent_name="gemini", rules=True, output_dir=str(output_dir))

    assert "commands" in results
    assert "rules" in results
    assert len(results["commands"]) == 2


def test_transpiler_generate_mcp_only_method(tmp_path) -> None:
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

    mcp_file = transpiler.generate_mcp("cursor", str(output_dir))

    assert Path(mcp_file).exists()


def test_transpiler_generate_rules_only_method(tmp_path) -> None:
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

    rules_files = transpiler.generate_rules("claude", str(output_dir))

    assert isinstance(rules_files, list)
    assert len(rules_files) >= 1
    assert Path(rules_files[0]).exists()

    rules_files = transpiler.generate_rules("windsurf", str(output_dir))

    assert isinstance(rules_files, list)
    assert len(rules_files) >= 1
    assert Path(rules_files[0]).exists()


def test_transpiler_unknown_agent_raises_value_error(tmp_path) -> None:
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
        transpiler.generate(agent_name="nonexistent", output_dir="/tmp")


def test_transpiler_creates_nested_output_directories(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", output_dir=str(output_dir))

    assert output_dir.exists()
    command_file = Path(results["commands"][0])
    assert command_file.exists()


def test_transpiler_generate_with_commands_disabled(tmp_path) -> None:
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

    results = transpiler.generate(agent_name="claude", commands=False, mcp=True, output_dir=str(output_dir))

    assert "commands" not in results
    assert "mcp" in results
    assert len(results["mcp"]) == 1


def test_transpiler_default_generates_only_commands(tmp_path) -> None:
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

    # Without any flags, only commands are generated (mcp and rules are False by default)
    results = transpiler.generate(agent_name="claude", output_dir=str(output_dir))

    assert "commands" in results
    assert "mcp" not in results
    assert "rules" not in results


def test_transpiler_with_dot_charlie_directory_regression_test(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

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

    transpiler = CommandTranspiler(str(charlie_dir))

    assert len(transpiler.config.commands) == 1
    assert transpiler.config.commands[0].name == "test"

    assert transpiler.root_dir == str(tmp_path.resolve())

    output_dir = tmp_path / "output"
    results = transpiler.generate(agent_name="cursor", output_dir=str(output_dir))

    assert "commands" in results
    assert len(results["commands"]) == 1

    generated_file = output_dir / ".cursor" / "commands" / "test.md"

    assert generated_file.exists()

    content = generated_file.read_text()
    assert "Test command" in content
    assert "Test prompt content" in content
