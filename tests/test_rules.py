"""Tests for rules file generator."""

from pathlib import Path

from charlie.agents.registry import get_agent_spec
from charlie.rules import (
    _extract_manual_additions,
    _format_command_reference,
    generate_rules_for_agents,
)
from charlie.schema import CharlieConfig, Command, CommandScripts, ProjectConfig, RulesConfig


def test_format_command_reference() -> None:
    command = Command(
        name="init",
        description="Initialize feature",
        prompt="Test",
        scripts=CommandScripts(sh="init.sh", ps="init.ps1"),
    )

    result = _format_command_reference(command, "myapp")

    assert "### /myapp.init" in result
    assert "**Description**: Initialize feature" in result
    assert "**Usage**: `/myapp.init <input>`" in result
    assert "Bash: `init.sh`" in result
    assert "PowerShell: `init.ps1`" in result


def test_extract_manual_additions() -> None:
    content = """# Title

Some content

<!-- MANUAL ADDITIONS START -->
My custom rules here
More custom stuff
<!-- MANUAL ADDITIONS END -->

More content
"""

    result = _extract_manual_additions(content)
    assert "My custom rules here" in result
    assert "More custom stuff" in result


def test_extract_manual_additions_empty() -> None:
    content = "# Title\n\nSome content"

    result = _extract_manual_additions(content)
    assert result == ""


def test_generate_rules_for_agents_preserves_manual_additions(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="init",
                description="Initialize",
                prompt="Test",
                scripts=CommandScripts(sh="init.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("windsurf")

    # First generation
    rules_paths = generate_rules_for_agents(config, "windsurf", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    # Add manual content
    content = Path(rules_path).read_text()
    content = content.replace(
        "<!-- MANUAL ADDITIONS START -->",
        "<!-- MANUAL ADDITIONS START -->\nMy custom rule\nAnother custom rule",
    )
    Path(rules_path).write_text(content)

    # Regenerate
    rules_paths = generate_rules_for_agents(config, "windsurf", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    # Check manual additions are preserved
    new_content = Path(rules_path).read_text()
    assert "My custom rule" in new_content
    assert "Another custom rule" in new_content


def test_generate_rules_for_agents_custom_title(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        rules=RulesConfig(title="Custom Title"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("claude")
    rules_paths = generate_rules_for_agents(config, "claude", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    content = Path(rules_path).read_text()
    assert "# Custom Title" in content


def test_generate_rules_for_agents_without_commands(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        rules=RulesConfig(include_commands=False),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("claude")
    rules_paths = generate_rules_for_agents(config, "claude", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    content = Path(rules_path).read_text()
    assert "## Available Commands" not in content
    assert "/test.test" not in content


def test_generate_rules_for_agents_without_preserve(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        rules=RulesConfig(preserve_manual=False),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("claude")
    rules_paths = generate_rules_for_agents(config, "claude", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    content = Path(rules_path).read_text()
    assert "MANUAL ADDITIONS START" not in content


def test_generate_rules_for_agents(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("claude")

    results = generate_rules_for_agents(config, "claude", agent_spec, str(tmp_path))

    # Check both files exist (results now returns lists of paths)
    assert len(results) >= 1
    assert Path(results[0]).exists()


def test_rules_file_date_format(tmp_path) -> None:
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
    )

    agent_spec = get_agent_spec("claude")
    rules_paths = generate_rules_for_agents(config, "claude", agent_spec, str(tmp_path))
    rules_path = rules_paths[0]

    content = Path(rules_path).read_text()
    # Check date format YYYY-MM-DD
    import re

    assert re.search(r"Last updated: \d{4}-\d{2}-\d{2}", content)


def test_generate_rules_merged_mode_with_sections(tmp_path) -> None:
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                    alwaysApply=True,  # Cursor-specific
                    globs=["**/*.py"],  # Cursor-specific
                ),
                RulesSection(
                    title="Commit Messages",
                    content="Use conventional commits",
                    order=2,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(config, "cursor", agent_spec, str(tmp_path), mode="merged")

    assert len(rules_paths) == 1
    content = Path(rules_paths[0]).read_text()

    # Check frontmatter (from first section)
    assert "alwaysApply: true" in content
    assert "globs:" in content
    assert "**/*.py" in content

    # Check both sections are present
    assert "## Code Style" in content
    assert "Use Black for formatting" in content
    assert "## Commit Messages" in content
    assert "Use conventional commits" in content


def test_generate_rules_separate_mode(tmp_path) -> None:
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                    alwaysApply=True,
                ),
                RulesSection(
                    title="Commit Messages",
                    content="Use conventional commits",
                    order=2,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="separate",
    )

    # Should generate 2 separate files
    assert len(rules_paths) == 2

    # Check first file (code-style.md)
    style_file = [p for p in rules_paths if "code-style" in p][0]
    style_content = Path(style_file).read_text()
    assert "# Code Style" in style_content
    assert "Use Black for formatting" in style_content
    assert "alwaysApply: true" in style_content

    # Check second file (commit-messages.md)
    commit_file = [p for p in rules_paths if "commit-messages" in p][0]
    commit_content = Path(commit_file).read_text()
    assert "# Commit Messages" in commit_content
    assert "Use conventional commits" in commit_content


def test_generate_rules_replaces_agent_name_placeholder_merged_mode(tmp_path) -> None:
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Agent Information",
                    content="You are using {{agent_name}} as your AI assistant.",
                    order=1,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(config, "cursor", agent_spec, str(tmp_path), mode="merged")

    assert len(rules_paths) == 1
    content = Path(rules_paths[0]).read_text()

    # The {{agent_name}} placeholder should be replaced with "Cursor" (the agent's display name)
    assert "You are using Cursor as your AI assistant." in content
    # The placeholder itself should NOT be present
    assert "{{agent_name}}" not in content


def test_generate_rules_replaces_agent_name_placeholder_separate_mode(tmp_path) -> None:
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Agent Information",
                    content="You are using {{agent_name}} as your AI assistant. Welcome to {{agent_name}}!",
                    order=1,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("claude")
    rules_paths = generate_rules_for_agents(
        config,
        "claude",
        agent_spec,
        str(tmp_path),
        mode="separate",
    )

    assert len(rules_paths) == 1
    content = Path(rules_paths[0]).read_text()

    # The {{agent_name}} placeholder should be replaced with "Claude Code" (the agent's display name)
    assert "You are using Claude Code as your AI assistant." in content
    assert "Welcome to Claude Code!" in content
    # The placeholder itself should NOT be present
    assert "{{agent_name}}" not in content


def test_generate_rules_replaces_multiple_placeholders(tmp_path) -> None:
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Context",
                    content="Agent: {{agent_name}}, Commands: {{commands_dir}}, Root: {{root}}",
                    order=1,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="merged",
        root_dir="/project/root",
    )

    assert len(rules_paths) == 1
    content = Path(rules_paths[0]).read_text()

    # All placeholders should be replaced
    assert "Agent: Cursor" in content  # Cursor is the agent's display name
    assert "Commands: .cursor/commands" in content
    assert "Root: /project/root" in content
    # Placeholders should NOT be present
    assert "{{agent_name}}" not in content
    assert "{{commands_dir}}" not in content
    assert "{{root}}" not in content


def test_generate_rules_preserves_original_filename(tmp_path) -> None:
    from charlie.schema import RulesSection

    # Create sections with custom filenames (as would be loaded from directory-based config)
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                    filename="custom-style-guide.md",
                ),
                RulesSection(
                    title="Commit Messages",
                    content="Use conventional commits",
                    order=2,
                    filename="commit-messages.md",
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="separate",
    )

    # Should generate 2 files with the original base names but .mdc extension for Cursor
    assert len(rules_paths) == 2

    # Check that files use the original base names with .mdc extension
    filenames = [Path(p).name for p in rules_paths]
    assert "custom-style-guide.mdc" in filenames
    assert "commit-messages.mdc" in filenames
    # These should NOT be present (wrong extension or wrong name)
    assert "custom-style-guide.md" not in filenames
    assert "commit-messages.md" not in filenames
    assert "code-style.mdc" not in filenames

    # Verify content is correct
    style_file = [p for p in rules_paths if "custom-style-guide" in p][0]
    style_content = Path(style_file).read_text()
    assert "# Code Style" in style_content
    assert "Use Black for formatting" in style_content

    commit_file = [p for p in rules_paths if "commit-messages" in p][0]
    commit_content = Path(commit_file).read_text()
    assert "# Commit Messages" in commit_content
    assert "Use conventional commits" in commit_content


def test_generate_rules_preserves_description_field_in_frontmatter(tmp_path) -> None:
    from charlie.schema import RulesSection

    # Create sections with description fields (as supported by Cursor)
    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                    description="Guidelines for code formatting and style",
                    alwaysApply=True,
                ),
                RulesSection(
                    title="Testing",
                    content="Write tests for all features",
                    order=2,
                    description="Testing requirements and standards",
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="separate",
    )

    # Check that description is in frontmatter, not in body
    style_file = [p for p in rules_paths if "code-style" in p][0]
    style_content = Path(style_file).read_text()

    # Description should be in the frontmatter
    assert "description: Guidelines for code formatting and style" in style_content
    # Make sure it's in the frontmatter section (before the first ---...--- block ends)
    frontmatter_end = style_content.find("---\n\n")
    assert frontmatter_end > 0
    assert style_content[:frontmatter_end].count("description: Guidelines for code formatting and style") == 1

    # Verify title is in the body as a heading
    assert "# Code Style" in style_content
    assert "Use Black for formatting" in style_content


def test_load_and_regenerate_rules_preserves_description(tmp_path) -> None:
    """Test that loading rules from files and regenerating them preserves description field."""
    from charlie.parser import load_directory_config

    # Create a .charlie/rules directory with a rule that has description
    charlie_dir = tmp_path / ".charlie"
    rules_dir = charlie_dir / "rules"
    rules_dir.mkdir(parents=True)

    # Create a rule file with description in frontmatter
    rule_file = rules_dir / "code-style.md"
    rule_content = """---
title: "Code Style"
description: "Guidelines for code formatting and style"
order: 1
alwaysApply: true
---

Use Black for formatting with line length 100.
"""
    rule_file.write_text(rule_content)

    # Load the config (which will parse the rule)
    config = load_directory_config(tmp_path)

    # Verify the rule was loaded with description
    assert config.rules is not None
    assert len(config.rules.sections) == 1
    section = config.rules.sections[0]
    assert section.title == "Code Style"
    assert section.description == "Guidelines for code formatting and style"
    assert section.order == 1
    assert section.alwaysApply is True

    # Now regenerate the rules
    agent_spec = get_agent_spec("cursor")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(output_dir),
        mode="separate",
    )

    # Check the regenerated file
    generated_file = rules_paths[0]
    generated_content = Path(generated_file).read_text()

    # Verify the filename was changed from .md to .mdc for Cursor
    assert generated_file.endswith(".mdc"), f"Expected .mdc extension but got {generated_file}"
    assert "code-style.mdc" in generated_file

    # Description should still be in frontmatter
    assert "description: Guidelines for code formatting and style" in generated_content
    # Verify it's in the frontmatter section
    lines = generated_content.split("\n")
    in_frontmatter = False
    found_description = False
    for i, line in enumerate(lines):
        if i == 0 and line == "---":
            in_frontmatter = True
        elif in_frontmatter and line == "---":
            in_frontmatter = False
        elif in_frontmatter and "description: Guidelines for code formatting and style" in line:
            found_description = True

    assert found_description, "Description should be in frontmatter"


def test_generate_rules_merged_mode_preserves_description(tmp_path) -> None:
    """Test that description field is preserved in merged mode frontmatter."""
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                    description="Guidelines for code formatting and style",
                    alwaysApply=True,
                ),
                RulesSection(
                    title="Testing",
                    content="Write tests for all features",
                    order=2,
                    description="Testing requirements",
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")
    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="merged",
    )

    # Should generate 1 merged file
    assert len(rules_paths) == 1

    content = Path(rules_paths[0]).read_text()

    # In merged mode, only the first section's extra fields go in frontmatter
    # Check that description from first section is in frontmatter
    assert "description: Guidelines for code formatting and style" in content

    # Verify it's in the frontmatter at the top of the file
    lines = content.split("\n")
    in_frontmatter = False
    found_description_in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line == "---":
            in_frontmatter = True
        elif in_frontmatter and line == "---":
            break  # End of frontmatter
        elif in_frontmatter and "description:" in line:
            found_description_in_frontmatter = True

    assert found_description_in_frontmatter, "Description should be in frontmatter for merged mode"


def test_cursor_uses_mdc_extension_for_rules(tmp_path) -> None:
    """Test that Cursor generates .mdc files for rules in separate mode."""
    from charlie.schema import RulesSection

    config = CharlieConfig(
        version="1.0",
        project=ProjectConfig(name="test", command_prefix="test"),
        commands=[
            Command(
                name="test",
                description="Test",
                prompt="Test",
                scripts=CommandScripts(sh="test.sh"),
            )
        ],
        rules=RulesConfig(
            sections=[
                RulesSection(
                    title="Code Style",
                    content="Use Black for formatting",
                    order=1,
                ),
                RulesSection(
                    title="Testing",
                    content="Write tests",
                    order=2,
                ),
            ]
        ),
    )

    agent_spec = get_agent_spec("cursor")

    # Verify agent spec has correct extensions
    assert agent_spec.command_extension == ".md"
    assert agent_spec.rules_extension == ".mdc"

    rules_paths = generate_rules_for_agents(
        config,
        "cursor",
        agent_spec,
        str(tmp_path),
        mode="separate",
    )

    # Should generate 2 files with .mdc extension
    assert len(rules_paths) == 2

    # Check that all rules files have .mdc extension
    for path in rules_paths:
        assert path.endswith(".mdc"), f"Expected .mdc extension but got {path}"
        assert Path(path).exists()

    # Verify the actual filenames
    filenames = [Path(p).name for p in rules_paths]
    assert "code-style.mdc" in filenames
    assert "testing.mdc" in filenames
