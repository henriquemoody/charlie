import pytest

from charlie.config_reader import (
    ConfigParseError,
    discover_charlie_files,
    find_config_file,
    load_directory_config,
    parse_config,
    parse_frontmatter,
    parse_single_file,
)
from charlie.schema import Command


def test_parse_valid_config_with_project_and_commands(tmp_path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
version: "1.0"
project:
  name: "test-project"
  namespace: "test"
commands:
  - name: "init"
    description: "Initialize"
    prompt: "Test prompt"
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
  namespace: "test"
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
"""
    )

    config = parse_config(config_file)
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "server1"
    assert config.mcp_servers[0].env["DEBUG"] == "true"


def test_parse_single_file_invalid_raises_config_parse_error(tmp_path) -> None:
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("name: test\n# missing required fields")

    with pytest.raises(ConfigParseError, match="Validation failed"):
        parse_single_file(invalid_file, Command)


def test_discover_config_files_empty_when_charlie_dir_not_exist(tmp_path) -> None:
    result = discover_charlie_files(tmp_path)
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

    result = discover_charlie_files(tmp_path)
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
  namespace: "myapp"
"""
    )

    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "init.md").write_text(
        """---
name: "init"
description: "Init"
---

Init prompt content
"""
    )

    config = load_directory_config(tmp_path)
    assert config.project is not None
    assert config.project.name == "my-project"
    assert config.project.namespace == "myapp"
    assert len(config.commands) == 1


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
# Commands field no longer exists in prototype
"""
    )

    (commands_dir / "init.yaml").write_text(
        """
name: "init"
description: "Init"
prompt: "Init"
"""
    )

    config = load_directory_config(tmp_path)
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "local-tools"
    # Commands field no longer exists in prototype


def test_should_infer_mcp_server_name_from_filename_when_name_not_provided(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    mcp_dir = charlie_dir / "mcp-servers"
    commands_dir = charlie_dir / "commands"
    mcp_dir.mkdir(parents=True)
    commands_dir.mkdir(parents=True)

    (mcp_dir / "my-custom-server.yaml").write_text(
        """
command: "node"
args: ["server.js"]
"""
    )

    (commands_dir / "init.yaml").write_text(
        """
name: "init"
description: "Init"
prompt: "Init"
"""
    )

    config = load_directory_config(tmp_path)

    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "my-custom-server"


def test_parse_config_detects_directory_based_format(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    commands_dir = charlie_dir / "commands"
    commands_dir.mkdir(parents=True)

    (commands_dir / "test.md").write_text(
        """---
name: "test"
description: "Test"
---

Test prompt content
"""
    )

    (tmp_path / "charlie.yaml").write_text(
        """
version: "1.0"
project:
  name: "test"
  namespace: "test"
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
  namespace: "test"
commands:
  - name: "init"
    description: "Init"
    prompt: "Init"
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


def test_discover_assets_recursively(tmp_path) -> None:
    """Regression test: ensure assets are discovered recursively from subdirectories."""
    # Create directory structure with nested assets
    charlie_dir = tmp_path / ".charlie"
    assets_dir = charlie_dir / "assets"
    subdirectory = assets_dir / "images"
    nested_subdirectory = subdirectory / "icons"

    assets_dir.mkdir(parents=True)
    subdirectory.mkdir(parents=True)
    nested_subdirectory.mkdir(parents=True)

    # Create files at different levels
    (assets_dir / "root-file.txt").write_text("root")
    (assets_dir / "data.json").write_text("{}")
    (subdirectory / "logo.png").write_text("png content")
    (subdirectory / "banner.jpg").write_text("jpg content")
    (nested_subdirectory / "favicon.ico").write_text("ico content")

    result = discover_charlie_files(tmp_path)

    # Should find all assets recursively
    assert len(result["assets"]) == 5

    # Verify all files are found
    asset_names = [asset.name for asset in result["assets"]]
    assert "root-file.txt" in asset_names
    assert "data.json" in asset_names
    assert "logo.png" in asset_names
    assert "banner.jpg" in asset_names
    assert "favicon.ico" in asset_names

    # Verify paths include subdirectories
    asset_paths = [str(asset) for asset in result["assets"]]
    assert any("images" in path for path in asset_paths)
    assert any("icons" in path for path in asset_paths)


def test_should_read_patterns_from_charlieignore_when_file_exists(tmp_path) -> None:
    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("*.log\n.env\nsecrets/\n")

    from charlie.config_reader import read_ignore_patterns

    patterns = read_ignore_patterns(tmp_path)

    assert patterns == ["*.log", ".env", "secrets/"]


def test_should_skip_comments_and_empty_lines_when_reading_charlieignore(tmp_path) -> None:
    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("# This is a comment\n*.log\n\n# Another comment\n.env\n   \nsecrets/\n")

    from charlie.config_reader import read_ignore_patterns

    patterns = read_ignore_patterns(tmp_path)

    assert patterns == ["*.log", ".env", "secrets/"]


def test_should_strip_whitespace_from_patterns_when_reading_charlieignore(tmp_path) -> None:
    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("  *.log  \n\t.env\t\n   secrets/   \n")

    from charlie.config_reader import read_ignore_patterns

    patterns = read_ignore_patterns(tmp_path)

    assert patterns == ["*.log", ".env", "secrets/"]


def test_should_return_empty_list_when_charlieignore_does_not_exist(tmp_path) -> None:
    from charlie.config_reader import read_ignore_patterns

    patterns = read_ignore_patterns(tmp_path)

    assert patterns == []


def test_should_include_charlie_and_charlieignore_patterns_when_no_yaml_patterns(tmp_path) -> None:
    config_file = tmp_path / "charlie.yaml"
    config_file.write_text("project:\n  name: TestProject\n")

    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("*.log\n.env\n")

    from charlie.config_reader import parse_config

    config = parse_config(config_file)

    assert config.ignore_patterns == [".charlie", "*.log", ".env"]


def test_should_merge_charlie_yaml_and_charlieignore_patterns_when_both_exist(tmp_path) -> None:
    config_file = tmp_path / "charlie.yaml"
    config_file.write_text("project:\n  name: TestProject\nignore_patterns:\n  - from_yaml.log\n  - shared.log\n")

    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("from_charlieignore.log\nshared.log\n")

    from charlie.config_reader import parse_config

    config = parse_config(config_file)

    assert config.ignore_patterns == [".charlie", "from_yaml.log", "shared.log", "from_charlieignore.log"]


def test_should_include_charlie_and_charlieignore_when_directory_config_has_no_yaml_patterns(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    charlie_dir.mkdir()

    config_file = charlie_dir / "charlie.yaml"
    config_file.write_text("project:\n  name: TestProject\n")

    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("*.log\n.env\n")

    from charlie.config_reader import load_directory_config

    config = load_directory_config(tmp_path)

    assert config.ignore_patterns == [".charlie", "*.log", ".env"]


def test_should_merge_charlie_yaml_and_charlieignore_when_directory_config_has_both(tmp_path) -> None:
    charlie_dir = tmp_path / ".charlie"
    charlie_dir.mkdir()

    config_file = tmp_path / "charlie.yaml"
    config_file.write_text("project:\n  name: TestProject\nignore_patterns:\n  - yaml_pattern.log\n")

    charlieignore_file = tmp_path / ".charlieignore"
    charlieignore_file.write_text("file_pattern.log\nyaml_pattern.log\n")

    from charlie.config_reader import load_directory_config

    config = load_directory_config(tmp_path)

    assert config.ignore_patterns == [".charlie", "yaml_pattern.log", "file_pattern.log"]
