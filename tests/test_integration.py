import json
from pathlib import Path


def test_complete_workflow_yaml_to_all_outputs(tmp_path) -> None:
    from charlie import CommandTranspiler

    config_file = tmp_path / "charlie.yaml"
    config_file.write_text(
        """
version: "1.0"

project:
  name: "integration-test"
  command_prefix: "test"

mcp_servers:
  - name: "test-server"
    command: "node"
    args: ["server.js"]
    env:
      DEBUG: "true"

rules:
  title: "Test Guidelines"
  include_commands: true
  preserve_manual: true

commands:
  - name: "init"
    description: "Initialize feature"
    prompt: |
      User: {{user_input}}
      Run: {{script}}
    scripts:
      sh: "init.sh"
      ps: "init.ps1"

  - name: "build"
    description: "Build project"
    prompt: "Build with {{script}}"
    scripts:
      sh: "build.sh"
"""
    )

    transpiler = CommandTranspiler(str(config_file))

    output_dir = tmp_path / "output"
    results = transpiler.generate(
        agent_name="claude",
        mcp=True,
        rules=True,
        output_dir=str(output_dir),
    )

    assert "commands" in results
    assert len(results["commands"]) == 2

    assert "mcp" in results
    mcp_file = Path(results["mcp"][0])
    assert mcp_file.exists()

    with open(mcp_file) as f:
        mcp_config = json.load(f)
    assert "test-server" in mcp_config["mcpServers"]
    assert len(mcp_config["mcpServers"]["test-server"]["capabilities"]["tools"]["list"]) == 2

    assert "rules" in results
    claude_rules = Path(results["rules"][0])
    assert claude_rules.exists()

    rules_content = claude_rules.read_text()
    assert "Test Guidelines" in rules_content
    assert "/test.init" in rules_content
    assert "/test.build" in rules_content
    assert "MANUAL ADDITIONS START" in rules_content

    results = transpiler.generate(agent_name="gemini", output_dir=str(output_dir))
    assert "commands" in results
    assert len(results["commands"]) == 2

    # Generate for Windsurf with rules
    results = transpiler.generate(agent_name="windsurf", rules=True, output_dir=str(output_dir))
    assert "commands" in results
    assert "rules" in results

    assert (output_dir / ".claude" / "commands").exists()
    assert (output_dir / ".gemini" / "commands").exists()
    assert (output_dir / ".windsurf" / "workflows").exists()
    assert (output_dir / "mcp-config.json").exists()


def test_library_api_usage_as_library(tmp_path) -> None:
    from charlie import CommandTranspiler

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "lib-test"
  command_prefix: "lib"
commands:
  - name: "test"
    description: "Test"
    prompt: "Test {{user_input}}"
    scripts:
      sh: "test.sh"
"""
    )

    transpiler = CommandTranspiler(str(config_file))

    output_dir = tmp_path / "output"
    results = transpiler.generate(agent_name="claude", output_dir=str(output_dir))

    assert "commands" in results
    assert len(results["commands"]) == 1

    command_file = Path(results["commands"][0])
    content = command_file.read_text()
    assert "description: Test" in content
    assert "$ARGUMENTS" in content


def test_spec_kit_example_workflow_similar_to_real_usage(tmp_path) -> None:
    import shutil

    from charlie import CommandTranspiler

    example_config = Path(__file__).parent.parent / "examples" / "speckit.yaml"
    config_file = tmp_path / "speckit.yaml"
    shutil.copy(example_config, config_file)

    transpiler = CommandTranspiler(str(config_file))

    output_dir = tmp_path / "output"
    results = transpiler.generate(
        agent_name="claude",
        mcp=True,
        rules=True,
        output_dir=str(output_dir),
    )

    assert len(results) > 0

    claude_commands = [Path(f) for f in results["commands"]]
    command_names = [f.stem for f in claude_commands]

    assert any("specify" in name for name in command_names)
    assert any("plan" in name for name in command_names)
    assert any("constitution" in name for name in command_names)

    results = transpiler.generate(agent_name="copilot", output_dir=str(output_dir))
    assert "commands" in results

    results = transpiler.generate(agent_name="cursor", output_dir=str(output_dir))
    assert "commands" in results
