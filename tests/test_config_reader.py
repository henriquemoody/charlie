import pytest

from charlie.config_reader import (
    ConfigParseError,
    discover_config_files,
    find_config_file,
    load_directory_config,
    parse_config,
    parse_frontmatter,
    parse_single_file,
)
from charlie.schema import Command, RulesSection


def test_parse_valid_config_with_project_and_commands(tmp_path) -> None:
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


def test_parse_nonexistent_file_creates_default_config_with_inferred_name(tmp_path) -> None:
    config = parse_config(tmp_path / "nonexistent.yaml")
    assert config.project is not None
    assert config.project.name == tmp_path.name
    assert config.version == "1.0"
    assert config.commands == []


def test_parse_empty_file_creates_default_config_with_inferred_name(tmp_path) -> None:
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")

    config = parse_config(config_file)
    assert config.project is not None
    assert config.project.name == tmp_path.name
    assert config.version == "1.0"
    assert config.commands == []


def test_parse_invalid_yaml_raises_config_parse_error(tmp_path) -> None:
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError, match="Invalid YAML syntax"):
        parse_config(config_file)


def test_parse_invalid_schema_raises_config_parse_error(tmp_path) -> None:
    config_file = tmp_path / "invalid_schema.yaml"
    config_file.write_text(
        """
version: "2.0"  # Invalid version
project:
  name: "test"
"""
    )

    with pytest.raises(ConfigParseError, match="validation failed"):
        parse_config(config_file)


def test_find_config_charlie_yaml_file(tmp_path) -> None:
    config_file = tmp_path / "charlie.yaml"
    config_file.write_text("test")

    found = find_config_file(tmp_path)
    assert found == config_file


def test_find_config_hidden_charlie_yaml_file(tmp_path) -> None:
    config_file = tmp_path / ".charlie.yaml"
    config_file.write_text("test")

    found = find_config_file(tmp_path)
    assert found == config_file


def test_find_config_prefers_non_hidden_over_hidden(tmp_path) -> None:
    visible = tmp_path / "charlie.yaml"
    hidden = tmp_path / ".charlie.yaml"
    visible.write_text("visible")
    hidden.write_text("hidden")

    found = find_config_file(tmp_path)
    assert found == visible


def test_find_config_not_found_returns_none(tmp_path) -> None:
    found = find_config_file(tmp_path)
    assert found is None


def test_parse_config_with_mcp_servers(tmp_path) -> None:
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


def test_parse_single_file_command_with_scripts(tmp_path) -> None:
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


def test_parse_single_file_rules_section_with_pass_through_fields(tmp_path) -> None:
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


def test_parse_single_file_invalid_raises_config_parse_error(tmp_path) -> None:
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("name: test\n# missing required fields")

    with pytest.raises(ConfigParseError, match="Validation failed"):
        parse_single_file(invalid_file, Command)


def test_discover_config_files_empty_when_charlie_dir_not_exist(tmp_path) -> None:
    result = discover_config_files(tmp_path)
    assert result["commands"] == []
    assert result["rules"] == []
    assert result["mcp_servers"] == []


def test_discover_config_files_complete_directory_structure(tmp_path) -> None:
    # Create directory structure
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    rules_dir = charlie_dir / "rules"
    mcp_dir = charlie_dir / "mcp-servers"

    commands_dir.mkdir(parents=True)
    rules_dir.mkdir(parents=True)
    mcp_dir.mkdir(parents=True)

    (commands_dir / "init.md").write_text("test")
    (commands_dir / "build.md").write_text("test")
    (rules_dir / "style.md").write_text("test")
    (mcp_dir / "server.yaml").write_text("test")

    result = discover_config_files(tmp_path)
    assert len(result["commands"]) == 2
    assert len(result["rules"]) == 1
    assert len(result["mcp_servers"]) == 1


def test_load_directory_config_minimal_with_inferred_project_name(tmp_path) -> None:
    # Create structure
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

    config = load_directory_config(tmp_path)
    assert config.version == "1.0"
    # Project config created with inferred name
    assert config.project is not None
    assert config.project.name == tmp_path.name
    assert len(config.commands) == 1
    assert config.commands[0].name == "test"


def test_load_directory_config_with_project_metadata(tmp_path) -> None:
    (tmp_path / "charlie.yaml").write_text(
        """
version: "1.0"
project:
  name: "my-project"
  command_prefix: "myapp"
"""
    )

    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "init.md").write_text(
        """---
name: "init"
description: "Init"
scripts:
  sh: "init.sh"
---

Init prompt content
"""
    )

    config = load_directory_config(tmp_path)
    assert config.project is not None
    assert config.project.name == "my-project"
    assert config.project.command_prefix == "myapp"
    assert len(config.commands) == 1


def test_load_directory_config_with_rules_sections(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    rules_dir = charlie_dir / "rules"
    commands_dir = charlie_dir / "commands"
    rules_dir.mkdir(parents=True)
    commands_dir.mkdir(parents=True)

    (rules_dir / "style.md").write_text(
        """---
title: "Code Style"
order: 1
---

Use Black
"""
    )

    (rules_dir / "commits.md").write_text(
        """---
title: "Commit Messages"
order: 2
---

Use conventional commits
"""
    )

    (commands_dir / "test.md").write_text(
        """---
name: "test"
description: "Test"
scripts:
  sh: "test.sh"
---

Test prompt content
"""
    )

    config = load_directory_config(tmp_path)
    assert config.rules is not None
    assert config.rules.sections is not None
    assert len(config.rules.sections) == 2
    titles = [s.title for s in config.rules.sections]
    assert "Code Style" in titles
    assert "Commit Messages" in titles


def test_load_directory_config_with_mcp_servers(tmp_path) -> None:
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


def test_parse_config_detects_directory_based_format(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

    (commands_dir / "test.md").write_text(
        """---
name: "test"
description: "Test"
scripts:
  sh: "test.sh"
---

Test prompt content
"""
    )

    (tmp_path / "charlie.yaml").write_text(
        """
version: "1.0"
project:
  name: "test"
  command_prefix: "test"
"""
    )

    config = parse_config(tmp_path / "charlie.yaml")
    assert len(config.commands) == 1
    assert config.commands[0].name == "test"


def test_parse_config_fallback_to_monolithic_without_charlie_dir(tmp_path) -> None:
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


def test_parse_frontmatter_valid_yaml_with_content(tmp_path) -> None:
    content = """---
name: "test"
description: "Test command"
---

Content body here
"""
    frontmatter, body = parse_frontmatter(content)
    assert frontmatter["name"] == "test"
    assert frontmatter["description"] == "Test command"
    assert body.strip() == "Content body here"


def test_parse_frontmatter_no_frontmatter_returns_empty_dict(tmp_path) -> None:
    content = "Just plain content"
    frontmatter, body = parse_frontmatter(content)
    assert frontmatter == {}
    assert body == "Just plain content"


def test_parse_frontmatter_empty_frontmatter_returns_empty_dict(tmp_path) -> None:
    content = """---
---

Content body
"""
    frontmatter, body = parse_frontmatter(content)
    assert frontmatter == {}
    assert body.strip() == "Content body"


def test_parse_frontmatter_complex_yaml_with_nested_structures(tmp_path) -> None:
    content = """---
name: "test"
tags:
  - tag1
  - tag2
scripts:
  sh: "test.sh"
  ps: "test.ps1"
---

# Content

With markdown formatting
"""
    frontmatter, body = parse_frontmatter(content)
    assert frontmatter["name"] == "test"
    assert frontmatter["tags"] == ["tag1", "tag2"]
    assert frontmatter["scripts"]["sh"] == "test.sh"
    assert "# Content" in body


def test_parse_frontmatter_invalid_yaml_raises_config_parse_error(tmp_path) -> None:
    content = """---
name: "test
invalid yaml: [unclosed
---

Content
"""
    with pytest.raises(ConfigParseError, match="Invalid YAML in frontmatter"):
        parse_frontmatter(content)


def test_parse_frontmatter_missing_closing_delimiter_raises_error(tmp_path) -> None:
    content = """---
name: "test"

No closing delimiter
"""
    with pytest.raises(ConfigParseError, match="closing delimiter"):
        parse_frontmatter(content)


def test_parse_single_file_markdown_command_with_frontmatter(tmp_path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """---
name: "test"
description: "Test command"
scripts:
  sh: "test.sh"
---

Test prompt content
"""
    )

    command = parse_single_file(md_file, Command)
    assert command.name == "test"
    assert command.description == "Test command"
    assert command.prompt == "Test prompt content"
    assert command.scripts.sh == "test.sh"


def test_parse_single_file_markdown_rules_with_frontmatter(tmp_path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """---
title: "Test Rule"
order: 1
---

Rule content here
"""
    )

    rules = parse_single_file(md_file, RulesSection)
    assert rules.title == "Test Rule"
    assert rules.order == 1
    assert rules.content == "Rule content here"
