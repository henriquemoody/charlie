import pytest

from charlie.config_merger import (
    merge_config_chain,
    merge_configs,
)
from charlie.schema import (
    CharlieConfig,
    Command,
    Project,
    Rule,
    StdioMCPServer,
)


@pytest.fixture
def base_project() -> Project:
    return Project(name="base-project", namespace="base", dir="/base")


@pytest.fixture
def overlay_project() -> Project:
    return Project(name="overlay-project", namespace="overlay", dir="/overlay")


@pytest.fixture
def base_config(base_project: Project) -> CharlieConfig:
    return CharlieConfig(
        version="1.0",
        project=base_project,
        commands=[
            Command(name="cmd1", description="Base command 1", prompt="Prompt 1"),
            Command(name="cmd2", description="Base command 2", prompt="Prompt 2"),
        ],
        rules=[
            Rule(name="rule1", description="Base rule 1", prompt="Rule prompt 1"),
        ],
        mcp_servers=[
            StdioMCPServer(name="server1", command="node", args=["base.js"]),
        ],
        variables={"var1": None, "var2": None},
        ignore_patterns=["*.log", "tmp/"],
    )


@pytest.fixture
def overlay_config(overlay_project: Project) -> CharlieConfig:
    return CharlieConfig(
        version="1.0",
        project=overlay_project,
        commands=[
            Command(name="cmd2", description="Overlay command 2", prompt="Overlay prompt 2"),
            Command(name="cmd3", description="Overlay command 3", prompt="Prompt 3"),
        ],
        rules=[
            Rule(name="rule2", description="Overlay rule 2", prompt="Rule prompt 2"),
        ],
        mcp_servers=[
            StdioMCPServer(name="server2", command="node", args=["overlay.js"]),
        ],
        variables={"var2": None, "var3": None},
        ignore_patterns=["*.log", "dist/"],
    )


def test_should_use_overlay_project_when_merging_configs(
    base_config: CharlieConfig, overlay_config: CharlieConfig
) -> None:
    result = merge_configs(base_config, overlay_config, source_name="overlay")

    assert result.config.project.name == "overlay-project"
    assert result.config.project.namespace == "overlay"


def test_should_merge_commands_when_no_duplicates(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        commands=[Command(name="cmd1", description="Cmd 1", prompt="P1")],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        commands=[Command(name="cmd2", description="Cmd 2", prompt="P2")],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.commands) == 2
    assert {cmd.name for cmd in result.config.commands} == {"cmd1", "cmd2"}
    assert len(result.warnings) == 0


def test_should_overwrite_command_when_duplicate_name_exists(
    base_config: CharlieConfig, overlay_config: CharlieConfig
) -> None:
    result = merge_configs(base_config, overlay_config, source_name="overlay")

    # cmd2 exists in both, overlay should win
    cmd2 = next(cmd for cmd in result.config.commands if cmd.name == "cmd2")
    assert cmd2.description == "Overlay command 2"
    assert cmd2.prompt == "Overlay prompt 2"


def test_should_emit_warning_when_command_is_overwritten(
    base_config: CharlieConfig, overlay_config: CharlieConfig
) -> None:
    result = merge_configs(base_config, overlay_config, source_name="overlay")

    assert any("Overwriting command 'cmd2'" in warning for warning in result.warnings)


def test_should_merge_rules_when_no_duplicates(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        rules=[Rule(name="rule1", description="Rule 1", prompt="P1")],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        rules=[Rule(name="rule2", description="Rule 2", prompt="P2")],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.rules) == 2
    assert {rule.name for rule in result.config.rules} == {"rule1", "rule2"}


def test_should_overwrite_rule_when_duplicate_name_exists(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        rules=[Rule(name="rule1", description="Base", prompt="Base prompt")],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        rules=[Rule(name="rule1", description="Overlay", prompt="Overlay prompt")],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.rules) == 1
    assert result.config.rules[0].description == "Overlay"
    assert any("Overwriting rule 'rule1'" in warning for warning in result.warnings)


def test_should_merge_mcp_servers_when_no_duplicates(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        mcp_servers=[StdioMCPServer(name="server1", command="node", args=["a.js"])],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        mcp_servers=[StdioMCPServer(name="server2", command="node", args=["b.js"])],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.mcp_servers) == 2


def test_should_overwrite_mcp_server_when_duplicate_name_exists(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        mcp_servers=[StdioMCPServer(name="server", command="node", args=["base.js"])],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        mcp_servers=[StdioMCPServer(name="server", command="node", args=["overlay.js"])],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert len(result.config.mcp_servers) == 1
    assert result.config.mcp_servers[0].args == ["overlay.js"]
    assert any("Overwriting MCP server 'server'" in warning for warning in result.warnings)


def test_should_merge_variables_when_no_duplicates(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        variables={"var1": None},
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        variables={"var2": None},
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert set(result.config.variables.keys()) == {"var1", "var2"}


def test_should_overwrite_variable_when_duplicate_key_exists(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        variables={"var1": None, "shared": None},
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        variables={"var2": None, "shared": None},
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert "shared" in result.config.variables
    assert any("Overwriting variable 'shared'" in warning for warning in result.warnings)


def test_should_deduplicate_ignore_patterns_when_merging(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        ignore_patterns=["*.log", "tmp/"],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        ignore_patterns=["*.log", "dist/"],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert result.config.ignore_patterns == ["*.log", "tmp/", "dist/"]


def test_should_deduplicate_assets_when_merging(base_project: Project) -> None:
    base = CharlieConfig(
        version="1.0",
        project=base_project,
        assets=["file1.txt", "file2.txt"],
    )
    overlay = CharlieConfig(
        version="1.0",
        project=base_project,
        assets=["file2.txt", "file3.txt"],
    )

    result = merge_configs(base, overlay, source_name="overlay")

    assert result.config.assets == ["file1.txt", "file2.txt", "file3.txt"]


def test_should_merge_chain_of_configs_in_order() -> None:
    project = Project(name="test", namespace=None, dir="/test")

    config1 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 1", prompt="P1")],
    )
    config2 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 2", prompt="P2")],
    )
    config3 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 3", prompt="P3")],
    )

    result = merge_config_chain(
        [
            (config1, "config1"),
            (config2, "config2"),
            (config3, "config3"),
        ]
    )

    # Last config should win
    assert result.config.commands[0].description == "Config 3"


def test_should_collect_all_warnings_when_merging_chain() -> None:
    project = Project(name="test", namespace=None, dir="/test")

    config1 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 1", prompt="P1")],
    )
    config2 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 2", prompt="P2")],
    )
    config3 = CharlieConfig(
        version="1.0",
        project=project,
        commands=[Command(name="cmd", description="Config 3", prompt="P3")],
    )

    result = merge_config_chain(
        [
            (config1, "config1"),
            (config2, "config2"),
            (config3, "config3"),
        ]
    )

    # Should have warnings from both merge steps
    assert len(result.warnings) == 2
    assert any("config2" in warning for warning in result.warnings)
    assert any("config3" in warning for warning in result.warnings)


def test_should_raise_error_when_merging_empty_chain() -> None:
    with pytest.raises(ValueError, match="Cannot merge empty config list"):
        merge_config_chain([])
