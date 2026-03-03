from pathlib import Path
from unittest.mock import Mock

import pytest

from charlie.assets_manager import AssetsManager
from charlie.config_merger import merge_configs
from charlie.config_reader import discover_charlie_files, load_directory_config, parse_single_file
from charlie.configurators.claude_configurator import ClaudeConfigurator
from charlie.configurators.copilot_configurator import CopilotConfigurator
from charlie.configurators.cursor_configurator import CursorConfigurator
from charlie.markdown_generator import MarkdownGenerator
from charlie.mcp_server_generator import MCPServerGenerator
from charlie.placeholder_transformer import PlaceholderTransformer
from charlie.schema import CharlieConfig, Project, Skill


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(name="test-project", namespace=None, dir=str(tmp_path))


@pytest.fixture
def project_with_namespace(tmp_path: Path) -> Project:
    return Project(name="test-project", namespace="myapp", dir=str(tmp_path))


@pytest.fixture
def tracker() -> Mock:
    return Mock()


@pytest.fixture
def markdown_generator() -> MarkdownGenerator:
    return MarkdownGenerator()


@pytest.fixture
def mcp_server_generator(tracker: Mock) -> MCPServerGenerator:
    return MCPServerGenerator(tracker)


@pytest.fixture
def assets_manager(tracker: Mock) -> AssetsManager:
    return AssetsManager(tracker)


@pytest.fixture
def claude_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> ClaudeConfigurator:
    return ClaudeConfigurator(project, tracker, markdown_generator, mcp_server_generator, assets_manager, "claude")


@pytest.fixture
def claude_configurator_with_namespace(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> ClaudeConfigurator:
    return ClaudeConfigurator(
        project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager, "claude"
    )


@pytest.fixture
def cursor_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> CursorConfigurator:
    return CursorConfigurator(project, tracker, markdown_generator, mcp_server_generator, assets_manager, "cursor")


@pytest.fixture
def cursor_configurator_with_namespace(
    project_with_namespace: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    mcp_server_generator: MCPServerGenerator,
    assets_manager: AssetsManager,
) -> CursorConfigurator:
    return CursorConfigurator(
        project_with_namespace, tracker, markdown_generator, mcp_server_generator, assets_manager, "cursor"
    )


@pytest.fixture
def copilot_configurator(
    project: Project,
    tracker: Mock,
    markdown_generator: MarkdownGenerator,
    assets_manager: AssetsManager,
) -> CopilotConfigurator:
    return CopilotConfigurator(project, tracker, markdown_generator, assets_manager, "copilot")


# ─── Claude configurator skills ──────────────────────────────────────────────


def test_claude_should_not_create_directory_when_no_skills(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    claude_configurator.skills([])

    skills_dir = Path(project.dir) / ".claude/skills"
    assert not skills_dir.exists()


def test_claude_should_create_skills_directory_when_skills_provided(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    claude_configurator.skills(skills)

    skills_dir = Path(project.dir) / ".claude/skills"
    assert skills_dir.exists()
    assert skills_dir.is_dir()


def test_claude_should_create_skill_subdirectory_for_each_skill(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [
        Skill(name="explain-code", description="Explains code", prompt="Explain the code"),
        Skill(name="fix-bug", description="Fixes bugs", prompt="Fix the bug"),
    ]

    claude_configurator.skills(skills)

    assert (Path(project.dir) / ".claude/skills/explain-code").is_dir()
    assert (Path(project.dir) / ".claude/skills/fix-bug").is_dir()


def test_claude_should_create_skill_md_file_in_subdirectory(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [
        Skill(name="explain-code", description="Explains code", prompt="Explain the code"),
        Skill(name="fix-bug", description="Fixes bugs", prompt="Fix the bug"),
    ]

    claude_configurator.skills(skills)

    assert (Path(project.dir) / ".claude/skills/explain-code/SKILL.md").exists()
    assert (Path(project.dir) / ".claude/skills/fix-bug/SKILL.md").exists()


def test_claude_should_write_prompt_to_skill_file_body(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [Skill(name="reviewer", description="Reviews code", prompt="Review the code carefully.")]

    claude_configurator.skills(skills)

    content = (Path(project.dir) / ".claude/skills/reviewer/SKILL.md").read_text()
    assert "Review the code carefully." in content


def test_claude_should_include_description_in_skill_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [Skill(name="reviewer", description="Reviews code for quality", prompt="Review the code")]

    claude_configurator.skills(skills)

    content = (Path(project.dir) / ".claude/skills/reviewer/SKILL.md").read_text()
    assert "description: Reviews code for quality" in content


def test_claude_should_include_name_in_skill_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    claude_configurator.skills(skills)

    content = (Path(project.dir) / ".claude/skills/explain-code/SKILL.md").read_text()
    assert "name: explain-code" in content


def test_claude_should_include_allowed_metadata_in_skill_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [
        Skill(
            name="deploy",
            description="Deploys the app",
            prompt="Deploy the app",
            metadata={"disable-model-invocation": True, "allowed-tools": "Bash(deploy.sh)"},
        )
    ]

    claude_configurator.skills(skills)

    content = (Path(project.dir) / ".claude/skills/deploy/SKILL.md").read_text()
    assert "disable-model-invocation: true" in content
    assert "allowed-tools: Bash(deploy.sh)" in content


def test_claude_should_exclude_unknown_metadata_from_skill_frontmatter(
    claude_configurator: ClaudeConfigurator, project: Project
) -> None:
    skills = [
        Skill(
            name="test-skill",
            description="Test",
            prompt="Test",
            metadata={"unknown-field": "value"},
        )
    ]

    claude_configurator.skills(skills)

    content = (Path(project.dir) / ".claude/skills/test-skill/SKILL.md").read_text()
    assert "unknown-field" not in content


def test_claude_should_prefix_skill_directory_with_namespace(
    claude_configurator_with_namespace: ClaudeConfigurator, project_with_namespace: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    claude_configurator_with_namespace.skills(skills)

    skill_dir = Path(project_with_namespace.dir) / ".claude/skills/myapp-explain-code"
    assert skill_dir.is_dir()
    assert (skill_dir / "SKILL.md").exists()


def test_claude_should_include_namespaced_name_in_skill_frontmatter(
    claude_configurator_with_namespace: ClaudeConfigurator, project_with_namespace: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    claude_configurator_with_namespace.skills(skills)

    content = (Path(project_with_namespace.dir) / ".claude/skills/myapp-explain-code/SKILL.md").read_text()
    assert "name: myapp-explain-code" in content


def test_claude_should_track_created_skill_files(
    claude_configurator: ClaudeConfigurator, tracker: Mock, project: Project
) -> None:
    skills = [Skill(name="reviewer", description="Reviews code", prompt="Review the code")]

    claude_configurator.skills(skills)

    tracker.track.assert_called_once()
    call_arg = tracker.track.call_args[0][0]
    assert "SKILL.md" in call_arg


# ─── Cursor configurator skills ──────────────────────────────────────────────


def test_cursor_should_not_create_directory_when_no_skills(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    cursor_configurator.skills([])

    skills_dir = Path(project.dir) / ".cursor/skills"
    assert not skills_dir.exists()


def test_cursor_should_create_skills_directory_when_skills_provided(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    cursor_configurator.skills(skills)

    skills_dir = Path(project.dir) / ".cursor/skills"
    assert skills_dir.exists()
    assert skills_dir.is_dir()


def test_cursor_should_create_skill_subdirectory_for_each_skill(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [
        Skill(name="explain-code", description="Explains code", prompt="Explain the code"),
        Skill(name="fix-bug", description="Fixes bugs", prompt="Fix the bug"),
    ]

    cursor_configurator.skills(skills)

    assert (Path(project.dir) / ".cursor/skills/explain-code").is_dir()
    assert (Path(project.dir) / ".cursor/skills/fix-bug").is_dir()


def test_cursor_should_create_skill_md_file_in_subdirectory(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    cursor_configurator.skills(skills)

    assert (Path(project.dir) / ".cursor/skills/explain-code/SKILL.md").exists()


def test_cursor_should_write_prompt_to_skill_file_body(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [Skill(name="reviewer", description="Reviews code", prompt="Review the code carefully.")]

    cursor_configurator.skills(skills)

    content = (Path(project.dir) / ".cursor/skills/reviewer/SKILL.md").read_text()
    assert "Review the code carefully." in content


def test_cursor_should_include_description_in_skill_frontmatter(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [Skill(name="reviewer", description="Reviews code for quality", prompt="Review the code")]

    cursor_configurator.skills(skills)

    content = (Path(project.dir) / ".cursor/skills/reviewer/SKILL.md").read_text()
    assert "description: Reviews code for quality" in content


def test_cursor_should_include_allowed_metadata_in_skill_frontmatter(
    cursor_configurator: CursorConfigurator, project: Project
) -> None:
    skills = [
        Skill(
            name="deploy",
            description="Deploys the app",
            prompt="Deploy the app",
            metadata={"disable-model-invocation": True, "license": "MIT"},
        )
    ]

    cursor_configurator.skills(skills)

    content = (Path(project.dir) / ".cursor/skills/deploy/SKILL.md").read_text()
    assert "disable-model-invocation: true" in content
    assert "license: MIT" in content


def test_cursor_should_prefix_skill_directory_with_namespace_dot_notation(
    cursor_configurator_with_namespace: CursorConfigurator, project_with_namespace: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    cursor_configurator_with_namespace.skills(skills)

    skill_dir = Path(project_with_namespace.dir) / ".cursor/skills/myapp.explain-code"
    assert skill_dir.is_dir()
    assert (skill_dir / "SKILL.md").exists()


def test_cursor_should_include_namespaced_name_in_skill_frontmatter(
    cursor_configurator_with_namespace: CursorConfigurator, project_with_namespace: Project
) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    cursor_configurator_with_namespace.skills(skills)

    content = (Path(project_with_namespace.dir) / ".cursor/skills/myapp.explain-code/SKILL.md").read_text()
    assert "name: myapp.explain-code" in content


# ─── Copilot configurator skills ─────────────────────────────────────────────


def test_copilot_should_skip_skills_and_track_message(copilot_configurator: CopilotConfigurator, tracker: Mock) -> None:
    skills = [Skill(name="explain-code", description="Explains code", prompt="Explain the code")]

    copilot_configurator.skills(skills)

    tracker.track.assert_called_once()
    call_arg = tracker.track.call_args[0][0]
    assert "does not support skills" in call_arg


def test_copilot_should_not_track_when_no_skills(copilot_configurator: CopilotConfigurator, tracker: Mock) -> None:
    copilot_configurator.skills([])

    tracker.track.assert_not_called()


# ─── Config reader: directory discovery ──────────────────────────────────────


def test_discover_charlie_files_should_return_empty_skills_when_no_skills_directory(
    tmp_path: Path,
) -> None:
    charlie_dir = tmp_path / ".charlie"
    charlie_dir.mkdir()

    discovered = discover_charlie_files(tmp_path)

    assert discovered["skills"] == []


def test_discover_charlie_files_should_discover_skill_files(
    tmp_path: Path,
) -> None:
    skills_dir = tmp_path / ".charlie" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "explain-code.md").write_text("---\ndescription: Explains code\n---\nExplain the code")
    (skills_dir / "fix-bug.md").write_text("---\ndescription: Fixes bugs\n---\nFix the bug")

    discovered = discover_charlie_files(tmp_path)

    skill_names = [f.name for f in discovered["skills"]]
    assert "explain-code.md" in skill_names
    assert "fix-bug.md" in skill_names


def test_parse_single_file_should_parse_skill_from_markdown(
    tmp_path: Path,
) -> None:
    skill_file = tmp_path / "explain-code.md"
    skill_file.write_text("---\ndescription: Explains code with diagrams\n---\nExplain the code with ASCII diagrams.")

    skill = parse_single_file(skill_file, Skill)

    assert skill.name == "explain-code"
    assert skill.description == "Explains code with diagrams"
    assert skill.prompt == "Explain the code with ASCII diagrams."


def test_parse_single_file_should_use_filename_as_skill_name_when_not_in_frontmatter(
    tmp_path: Path,
) -> None:
    skill_file = tmp_path / "my-skill.md"
    skill_file.write_text("---\ndescription: My skill\n---\nDo something.")

    skill = parse_single_file(skill_file, Skill)

    assert skill.name == "my-skill"


def test_parse_single_file_should_use_explicit_name_in_frontmatter(
    tmp_path: Path,
) -> None:
    skill_file = tmp_path / "my-skill.md"
    skill_file.write_text("---\nname: custom-name\ndescription: My skill\n---\nDo something.")

    skill = parse_single_file(skill_file, Skill)

    assert skill.name == "custom-name"


def test_parse_single_file_should_collect_extra_frontmatter_as_metadata(
    tmp_path: Path,
) -> None:
    skill_file = tmp_path / "my-skill.md"
    skill_file.write_text(
        "---\ndescription: My skill\ndisable-model-invocation: true\nallowed-tools: Bash\n---\nDo something."
    )

    skill = parse_single_file(skill_file, Skill)

    assert skill.metadata.get("disable-model-invocation") is True
    assert skill.metadata.get("allowed-tools") == "Bash"


def test_load_directory_config_should_load_skills_from_charlie_skills_directory(
    tmp_path: Path,
) -> None:
    skills_dir = tmp_path / ".charlie" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "explain-code.md").write_text(
        "---\ndescription: Explains code\n---\nExplain the code with ASCII diagrams."
    )

    config = load_directory_config(tmp_path)

    assert len(config.skills) == 1
    assert config.skills[0].name == "explain-code"
    assert config.skills[0].description == "Explains code"


# ─── Schema validation ────────────────────────────────────────────────────────


def test_charlie_config_should_reject_duplicate_skill_names() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Duplicate skill names"):
        CharlieConfig(
            project=Project(name="test", namespace=None, dir="."),
            skills=[
                Skill(name="my-skill", description="First", prompt="First"),
                Skill(name="my-skill", description="Second", prompt="Second"),
            ],
        )


# ─── Config merger ────────────────────────────────────────────────────────────


def test_merge_configs_should_combine_skills_from_both_configs() -> None:
    project = Project(name="test", namespace=None, dir=".")
    base = CharlieConfig(
        project=project,
        skills=[Skill(name="skill-a", description="Skill A", prompt="A")],
    )
    overlay = CharlieConfig(
        project=project,
        skills=[Skill(name="skill-b", description="Skill B", prompt="B")],
    )

    result = merge_configs(base, overlay)

    assert len(result.config.skills) == 2
    names = [s.name for s in result.config.skills]
    assert "skill-a" in names
    assert "skill-b" in names


def test_merge_configs_should_overlay_skill_with_same_name() -> None:
    project = Project(name="test", namespace=None, dir=".")
    base = CharlieConfig(
        project=project,
        skills=[Skill(name="my-skill", description="Base description", prompt="Base prompt")],
    )
    overlay = CharlieConfig(
        project=project,
        skills=[Skill(name="my-skill", description="Overlay description", prompt="Overlay prompt")],
    )

    result = merge_configs(base, overlay, source_name="overlay.yaml")

    assert len(result.config.skills) == 1
    assert result.config.skills[0].description == "Overlay description"


def test_merge_configs_should_warn_on_duplicate_skill_name() -> None:
    project = Project(name="test", namespace=None, dir=".")
    base = CharlieConfig(
        project=project,
        skills=[Skill(name="my-skill", description="Base", prompt="Base")],
    )
    overlay = CharlieConfig(
        project=project,
        skills=[Skill(name="my-skill", description="Overlay", prompt="Overlay")],
    )

    result = merge_configs(base, overlay, source_name="overlay.yaml")

    assert any("skill" in w and "my-skill" in w for w in result.warnings)


# ─── Placeholder transformer ──────────────────────────────────────────────────


def test_placeholder_transformer_should_transform_skill_prompt() -> None:
    project = Project(name="my-project", namespace=None, dir=".")
    transformer = PlaceholderTransformer(
        placeholders={"agent_name": "Claude Code", "skills_dir": ".claude/skills"},
        variables={},
        project=project,
    )
    skill = Skill(name="my-skill", description="My skill", prompt="Use {{agent_name}} to do things")

    result = transformer.skill(skill)

    assert result.prompt == "Use Claude Code to do things"


def test_placeholder_transformer_should_transform_skill_metadata() -> None:
    project = Project(name="my-project", namespace=None, dir=".")
    transformer = PlaceholderTransformer(
        placeholders={"agent_name": "Claude Code", "skills_dir": ".claude/skills"},
        variables={},
        project=project,
    )
    skill = Skill(
        name="my-skill",
        description="My skill",
        prompt="Do things",
        metadata={"description": "Use {{agent_name}}"},
    )

    result = transformer.skill(skill)

    assert result.metadata["description"] == "Use Claude Code"


def test_placeholder_transformer_should_preserve_skill_name_and_description() -> None:
    project = Project(name="my-project", namespace=None, dir=".")
    transformer = PlaceholderTransformer(
        placeholders={},
        variables={},
        project=project,
    )
    skill = Skill(name="my-skill", description="My fixed description", prompt="Do things")

    result = transformer.skill(skill)

    assert result.name == "my-skill"
    assert result.description == "My fixed description"
