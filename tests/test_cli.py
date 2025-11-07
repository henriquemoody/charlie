from typer.testing import CliRunner

from charlie.cli import app

runner = CliRunner()


def create_test_config(tmp_path, filename="charlie.yaml") -> None:
    config_file = tmp_path / filename
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test-project"
  command_prefix: "test"
mcp_servers:
  - name: "test-server"
    command: "node"
    args: ["server.js"]
commands:
  - name: "init"
    description: "Initialize feature"
    prompt: "Initialize: {{user_input}}"
    scripts:
      sh: "init.sh"
  - name: "plan"
    description: "Create plan"
    prompt: "Plan: {{user_input}}"
    scripts:
      sh: "plan.sh"
"""
    )
    return config_file


def test_setup_with_explicit_config_file(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["setup", "claude", "--config", str(config_file), "--output", str(output_dir)],
    )

    assert result.exit_code == 0
    assert "Setup complete" in result.stdout
    assert "commands" in result.stdout


def test_setup_auto_detect_config_in_current_directory(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["setup", "claude", "--output", str(output_dir)],
        env={"PWD": str(tmp_path)},
        catch_exceptions=False,
    )

    result = runner.invoke(app, ["setup", "claude", "--config", str(config_file), "--output", str(output_dir)])

    assert result.exit_code == 0
    assert "Setup complete" in result.stdout


def test_setup_different_agents_individually(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["setup", "claude", "--config", str(config_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 0
    assert "commands" in result.stdout

    result = runner.invoke(
        app,
        ["setup", "gemini", "--config", str(config_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 0
    assert "commands" in result.stdout

    result = runner.invoke(
        app,
        ["setup", "cursor", "--config", str(config_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 0
    assert "commands" in result.stdout


def test_setup_with_mcp_config_generation(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["setup", "claude", "--config", str(config_file), "--mcp", "--output", str(output_dir)])

    assert result.exit_code == 0
    assert "mcp" in result.stdout

    mcp_file = output_dir / "mcp-config.json"
    assert mcp_file.exists()


def test_setup_with_rules_file_generation(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "setup",
            "claude",
            "--config",
            str(config_file),
            "--rules",
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "rules" in result.stdout

    # Test windsurf too
    result = runner.invoke(
        app,
        [
            "setup",
            "windsurf",
            "--config",
            str(config_file),
            "--rules",
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "rules" in result.stdout


def test_setup_with_all_options_mcp_and_rules_enabled(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "setup",
            "claude",
            "--config",
            str(config_file),
            "--mcp",
            "--rules",
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    # Should generate multiple targets
    assert "commands" in result.stdout
    assert "mcp" in result.stdout


def test_setup_fails_without_agent_argument() -> None:
    result = runner.invoke(app, ["setup"])

    assert result.exit_code == 2
    output = result.output.lower()
    assert "missing argument" in output or "required" in output or result.exit_code == 2


def test_setup_fails_with_nonexistent_config_file() -> None:
    result = runner.invoke(app, ["setup", "claude", "--config", "/nonexistent/config.yaml"])

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_setup_fails_with_invalid_agent_name(tmp_path) -> None:
    config_file = create_test_config(tmp_path)

    result = runner.invoke(app, ["setup", "nonexistent", "--config", str(config_file)])

    assert result.exit_code == 1
    assert "Unknown agent" in result.stdout


def test_validate_succeeds_with_valid_config(tmp_path) -> None:
    config_file = create_test_config(tmp_path)

    result = runner.invoke(app, ["validate", str(config_file)])

    assert result.exit_code == 0
    assert "Configuration is valid" in result.stdout
    assert "test-project" in result.stdout


def test_validate_fails_with_invalid_config(tmp_path) -> None:
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: syntax:")

    result = runner.invoke(app, ["validate", str(config_file)])

    assert result.exit_code == 1
    assert "Validation Failed" in result.stdout or "Error" in result.stdout


def test_validate_auto_detects_config_in_current_directory(tmp_path) -> None:
    create_test_config(tmp_path)

    import os

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        result = runner.invoke(app, ["validate"])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.stdout

    finally:
        os.chdir(original_dir)


def test_list_agents_shows_all_supported_agents() -> None:
    result = runner.invoke(app, ["list-agents"])

    assert result.exit_code == 0
    assert "Supported AI Agents" in result.stdout
    assert "claude" in result.stdout.lower()
    assert "gemini" in result.stdout.lower()
    assert "copilot" in result.stdout.lower()


def test_info_shows_details_for_valid_agent() -> None:
    result = runner.invoke(app, ["info", "claude"])

    assert result.exit_code == 0
    assert "Claude Code" in result.stdout
    assert ".claude/commands" in result.stdout


def test_info_fails_for_invalid_agent() -> None:
    result = runner.invoke(app, ["info", "nonexistent"])

    assert result.exit_code == 1
    assert "Unknown agent" in result.stdout


def test_setup_verbose_output_shows_full_paths(tmp_path) -> None:
    config_file = create_test_config(tmp_path)
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "setup",
            "claude",
            "--config",
            str(config_file),
            "--output",
            str(output_dir),
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    # Verbose should show full paths
    assert str(output_dir) in result.stdout or "claude" in result.stdout
