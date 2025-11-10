import json
from pathlib import Path


def test_complete_workflow_yaml_to_all_outputs(tmp_path) -> None:
    from charlie import AgentConfigurator, AgentSpecRegistry
    from charlie.config_reader import parse_config

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
    commands: ["init", "build"]
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

    config = parse_config(str(config_file))
    output_dir = tmp_path / "output"
    registry = AgentSpecRegistry()

    claude_spec = registry.get("claude")
    configurator = AgentConfigurator.create(
        agent_spec=claude_spec, project_config=config.project, root_dir=str(tmp_path)
    )

    command_files = configurator.commands(config.commands, str(output_dir))
    assert len(command_files) == 2

    mcp_file = configurator.mcp_servers(config, str(output_dir))
    assert Path(mcp_file).exists()

    with open(mcp_file) as f:
        mcp_config = json.load(f)
    assert "test-server" in mcp_config["mcpServers"]
    assert len(mcp_config["mcpServers"]["test-server"]["capabilities"]["tools"]["list"]) == 2

    rules_files = configurator.rules(config, str(output_dir))
    assert len(rules_files) > 0
    claude_rules = Path(rules_files[0])
    assert claude_rules.exists()

    rules_content = claude_rules.read_text()
    assert "Test Guidelines" in rules_content
    assert "/test.init" in rules_content
    assert "/test.build" in rules_content
    assert "MANUAL ADDITIONS START" in rules_content

    gemini_spec = registry.get("gemini")
    gemini_configurator = AgentConfigurator.create(
        agent_spec=gemini_spec, project_config=config.project, root_dir=str(tmp_path)
    )
    gemini_commands = gemini_configurator.commands(config.commands, str(output_dir))
    assert len(gemini_commands) == 2

    windsurf_spec = registry.get("windsurf")
    windsurf_configurator = AgentConfigurator.create(
        agent_spec=windsurf_spec, project_config=config.project, root_dir=str(tmp_path)
    )
    windsurf_configurator.commands(config.commands, str(output_dir))
    windsurf_configurator.rules(config, str(output_dir))

    assert (output_dir / ".claude" / "commands").exists()
    assert (output_dir / ".gemini" / "commands").exists()
    assert (output_dir / ".windsurf" / "workflows").exists()
    assert (output_dir / ".claude" / "mcp.json").exists()


def test_library_api_usage_as_library(tmp_path) -> None:
    from charlie import AgentConfigurator, AgentSpecRegistry
    from charlie.config_reader import parse_config

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

    config = parse_config(str(config_file))
    registry = AgentSpecRegistry()
    claude_spec = registry.get("claude")

    configurator = AgentConfigurator.create(
        agent_spec=claude_spec, project_config=config.project, root_dir=str(tmp_path)
    )

    output_dir = tmp_path / "output"
    command_files = configurator.commands(config.commands, str(output_dir))

    assert len(command_files) == 1

    command_file = Path(command_files[0])
    content = command_file.read_text()
    assert "description: Test" in content
    assert "$ARGUMENTS" in content


def test_spec_kit_example_workflow_similar_to_real_usage(tmp_path) -> None:
    import shutil

    from charlie import AgentConfigurator, AgentSpecRegistry
    from charlie.config_reader import parse_config

    example_config = Path(__file__).parent.parent / "examples" / "speckit.yaml"
    config_file = tmp_path / "speckit.yaml"
    shutil.copy(example_config, config_file)

    config = parse_config(str(config_file))
    output_dir = tmp_path / "output"
    registry = AgentSpecRegistry()

    claude_spec = registry.get("claude")
    configurator = AgentConfigurator.create(
        agent_spec=claude_spec, project_config=config.project, root_dir=str(tmp_path)
    )

    command_files = configurator.commands(config.commands, str(output_dir))
    configurator.mcp_servers(config, str(output_dir))
    configurator.rules(config, str(output_dir))

    assert len(command_files) > 0

    claude_commands = [Path(f) for f in command_files]
    command_names = [f.stem for f in claude_commands]

    assert any("specify" in name for name in command_names)
    assert any("plan" in name for name in command_names)
    assert any("constitution" in name for name in command_names)

    copilot_spec = registry.get("copilot")
    copilot_configurator = AgentConfigurator.create(
        agent_spec=copilot_spec, project_config=config.project, root_dir=str(tmp_path)
    )
    copilot_commands = copilot_configurator.commands(config.commands, str(output_dir))
    assert len(copilot_commands) > 0

    cursor_spec = registry.get("cursor")
    cursor_configurator = AgentConfigurator.create(
        agent_spec=cursor_spec, project_config=config.project, root_dir=str(tmp_path)
    )
    cursor_commands = cursor_configurator.commands(config.commands, str(output_dir))
    assert len(cursor_commands) > 0
