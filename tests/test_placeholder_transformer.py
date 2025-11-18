import os
from pathlib import Path

import pytest

from charlie.enums import FileFormat, TransportType
from charlie.placeholder_transformer import (
    ChoiceNotFoundError,
    EnvironmentVariableNotFoundError,
    PlaceholderTransformer,
    VariableNotFoundError,
)
from charlie.schema import (
    Agent,
    ChoiceReplacement,
    Command,
    HttpMCPServer,
    Project,
    Rule,
    StdioMCPServer,
    ValueReplacement,
)


@pytest.fixture
def sample_agent() -> Agent:
    return Agent(
        name="Claude",
        shortname="claude",
        dir=".cursor",
        default_format=FileFormat.MARKDOWN,
        commands_dir=".cursor/commands",
        commands_extension=".md",
        commands_shorthand_injection="[Commands Injection]",
        rules_dir=".cursor/rules",
        rules_file=".cursor/rules/main.md",
        rules_extension=".md",
        mcp_file=".cursor/mcp.json",
    )


@pytest.fixture
def sample_project() -> Project:
    return Project(
        name="my-project",
        namespace="myproject",
        dir="/home/user/projects/my-project",
    )


@pytest.fixture
def sample_project_without_namespace() -> Project:
    return Project(
        name="my-project",
        namespace=None,
        dir="/home/user/projects/my-project",
    )


@pytest.fixture
def sample_variables() -> dict[str, str]:
    return {
        "language": "python",
        "framework": "fastapi",
        "database": "postgresql",
    }


@pytest.fixture
def transformer(
    sample_agent: Agent, sample_variables: dict[str, str], sample_project: Project
) -> PlaceholderTransformer:
    return PlaceholderTransformer(
        agent=sample_agent,
        variables=sample_variables,
        project=sample_project,
    )


class TestStaticPlaceholders:
    def test_should_replace_project_placeholders_when_text_contains_them(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Project: {{project_name}} in {{project_dir}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Project: my-project in /home/user/projects/my-project"

    def test_should_replace_agent_placeholders_when_text_contains_them(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Agent: {{agent_name}} ({{agent_shortname}})"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Agent: Claude (claude)"

    def test_should_replace_directory_placeholders_with_full_paths_when_not_in_project_dir(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Dirs: {{agent_dir}}, {{commands_dir}}, {{rules_dir}}, {{assets_dir}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == (
            "Dirs: /home/user/projects/my-project/.cursor, "
            "/home/user/projects/my-project/.cursor/commands, "
            "/home/user/projects/my-project/.cursor/rules, "
            "/home/user/projects/my-project/.cursor/assets"
        )

    def test_should_replace_directory_placeholders_with_relative_paths_when_in_project_dir(
        self, sample_agent: Agent, sample_variables: dict[str, str], tmp_path: Path
    ) -> None:
        project = Project(name="test-project", namespace="test", dir=str(tmp_path))
        transformer = PlaceholderTransformer(agent=sample_agent, variables=sample_variables, project=project)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            text = "Dirs: {{agent_dir}}, {{commands_dir}}, {{rules_dir}}, {{assets_dir}}"
            command = Command(name="test", description="test", prompt=text)

            result = transformer.command(command)

            assert result.prompt == ("Dirs: .cursor, .cursor/commands, .cursor/rules, .cursor/assets")
        finally:
            os.chdir(original_cwd)

    def test_should_replace_project_dir_with_dot_when_in_project_dir(
        self, sample_agent: Agent, sample_variables: dict[str, str], tmp_path: Path
    ) -> None:
        project = Project(name="test-project", namespace="test", dir=str(tmp_path))
        transformer = PlaceholderTransformer(agent=sample_agent, variables=sample_variables, project=project)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            text = "Project dir: {{project_dir}}"
            command = Command(name="test", description="test", prompt=text)

            result = transformer.command(command)

            assert result.prompt == "Project dir: ."
        finally:
            os.chdir(original_cwd)

    def test_should_replace_file_placeholders_when_text_contains_them(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Files: {{rules_file}}, {{mcp_file}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == (
            "Files: /home/user/projects/my-project/.cursor/rules/main.md, "
            "/home/user/projects/my-project/.cursor/mcp.json"
        )

    def test_should_replace_commands_shorthand_injection_when_text_contains_it(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Injection: {{commands_shorthand_injection}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Injection: [Commands Injection]"

    def test_should_replace_namespace_with_empty_string_when_namespace_is_none(
        self, sample_agent: Agent, sample_variables: dict[str, str], sample_project_without_namespace: Project
    ) -> None:
        transformer = PlaceholderTransformer(
            agent=sample_agent, variables=sample_variables, project=sample_project_without_namespace
        )
        text = "Namespace: '{{project_namespace}}'"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Namespace: ''"

    def test_should_replace_multiple_occurrences_of_same_placeholder_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "{{project_name}} - {{project_name}} - {{project_name}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "my-project - my-project - my-project"


class TestVariablePlaceholders:
    def test_should_replace_variable_placeholders_when_variables_exist(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Language: {{var:language}}, Framework: {{var:framework}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Language: python, Framework: fastapi"

    def test_should_leave_variable_placeholder_unchanged_when_variable_not_in_collection(
        self, transformer: PlaceholderTransformer
    ) -> None:
        text = "Unknown: {{var:unknown_variable}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Unknown: {{var:unknown_variable}}"

    def test_should_handle_empty_variables_dict_when_transforming(
        self, sample_agent: Agent, sample_project: Project
    ) -> None:
        transformer = PlaceholderTransformer(agent=sample_agent, variables={}, project=sample_project)
        text = "Language: {{var:language}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Language: {{var:language}}"


class TestEnvironmentVariablePlaceholders:
    def test_should_replace_environment_variable_when_it_exists(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MY_API_KEY", "secret-key-123")
        text = "API Key: {{env:MY_API_KEY}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "API Key: secret-key-123"

    def test_should_raise_error_when_environment_variable_not_found(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        text = "Value: {{env:NONEXISTENT_VAR}}"
        command = Command(name="test", description="test", prompt=text)

        with pytest.raises(EnvironmentVariableNotFoundError, match="NONEXISTENT_VAR"):
            transformer.command(command)

    def test_should_replace_multiple_environment_variables_when_they_exist(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VAR_ONE", "value1")
        monkeypatch.setenv("VAR_TWO", "value2")
        text = "Values: {{env:VAR_ONE}} and {{env:VAR_TWO}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Values: value1 and value2"

    def test_should_handle_environment_variables_with_underscores_and_numbers(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VAR_NAME_123", "test_value")
        text = "Value: {{env:VAR_NAME_123}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Value: test_value"


class TestReplacements:
    def test_should_replace_with_value_when_replacement_type_is_value(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {"api_version": ValueReplacement(value="v1.2.3")}
        text = "API Version: {{api_version}}"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        result = transformer.command(command)

        assert result.prompt == "API Version: v1.2.3"

    def test_should_replace_with_numeric_value_when_replacement_is_number(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {"port": ValueReplacement(value=8080)}
        text = "Port: {{port}}"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        result = transformer.command(command)

        assert result.prompt == "Port: 8080"

    def test_should_replace_with_boolean_value_when_replacement_is_boolean(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {"enabled": ValueReplacement(value=True)}
        text = "Enabled: {{enabled}}"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        result = transformer.command(command)

        assert result.prompt == "Enabled: True"

    def test_should_replace_with_choice_when_discriminator_variable_exists(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {
            "install_command": ChoiceReplacement(
                discriminator="language",
                options={"python": "pip install", "javascript": "npm install", "ruby": "gem install"},
            )
        }
        text = "Install: {{install_command}} my-package"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        result = transformer.command(command)

        assert result.prompt == "Install: pip install my-package"

    def test_should_raise_error_when_discriminator_variable_not_found(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {
            "install_command": ChoiceReplacement(discriminator="unknown_var", options={"python": "pip install"})
        }
        text = "Install: {{install_command}}"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        with pytest.raises(VariableNotFoundError, match="unknown_var"):
            transformer.command(command)

    def test_should_raise_error_when_choice_not_found_for_variable_value(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {
            "install_command": ChoiceReplacement(
                discriminator="language", options={"javascript": "npm install", "ruby": "gem install"}
            )
        }
        text = "Install: {{install_command}}"
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        with pytest.raises(ChoiceNotFoundError, match="python"):
            transformer.command(command)


class TestCommandTransformation:
    def test_should_transform_command_prompt_with_all_placeholder_types(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("API_KEY", "abc123")
        replacements = {"version": ValueReplacement(value="2.0")}
        command = Command(
            name="deploy",
            description="Deploy application",
            prompt="Deploy {{project_name}} using {{var:language}} v{{version}} with key {{env:API_KEY}}",
            replacements=replacements,
        )

        result = transformer.command(command)

        assert result.prompt == "Deploy my-project using python v2.0 with key abc123"
        assert result.name == "deploy"
        assert result.description == "Deploy application"

    def test_should_preserve_command_metadata_when_transforming(self, transformer: PlaceholderTransformer) -> None:
        metadata = {"category": "build", "priority": 1}
        command = Command(name="build", description="Build project", prompt="Build {{project_name}}", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata == metadata

    def test_should_transform_string_values_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "project": "{{project_name}}",
            "language": "{{var:language}}",
            "priority": 1,
        }
        command = Command(name="build", description="Build", prompt="Build", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["project"] == "my-project"
        assert result.metadata["language"] == "python"
        assert result.metadata["priority"] == 1

    def test_should_transform_nested_dict_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "config": {
                "project": "{{project_name}}",
                "framework": "{{var:framework}}",
            }
        }
        command = Command(name="build", description="Build", prompt="Build", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["config"]["project"] == "my-project"
        assert result.metadata["config"]["framework"] == "fastapi"

    def test_should_transform_list_items_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "tags": ["{{project_name}}", "{{var:language}}", "build"],
            "count": 3,
        }
        command = Command(name="build", description="Build", prompt="Build", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["tags"] == ["my-project", "python", "build"]
        assert result.metadata["count"] == 3

    def test_should_transform_deeply_nested_metadata_in_command_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "level1": {
                "level2": {
                    "level3": {
                        "project": "{{project_name}}",
                    }
                }
            }
        }
        command = Command(name="test", description="Test", prompt="Test", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["level1"]["level2"]["level3"]["project"] == "my-project"

    def test_should_transform_list_of_dicts_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "servers": [
                {"name": "{{project_name}}-api", "port": 8000},
                {"name": "{{project_name}}-worker", "port": 9000},
            ]
        }
        command = Command(name="deploy", description="Deploy", prompt="Deploy", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["servers"][0]["name"] == "my-project-api"
        assert result.metadata["servers"][0]["port"] == 8000
        assert result.metadata["servers"][1]["name"] == "my-project-worker"
        assert result.metadata["servers"][1]["port"] == 9000

    def test_should_transform_nested_lists_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "matrix": [
                ["{{project_name}}", "{{var:language}}"],
                ["{{var:framework}}", "test"],
            ]
        }
        command = Command(name="test", description="Test", prompt="Test", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["matrix"][0] == ["my-project", "python"]
        assert result.metadata["matrix"][1] == ["fastapi", "test"]

    def test_should_apply_replacements_to_command_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {"version": ValueReplacement(value="2.0")}
        metadata = {"release": "{{version}}", "stable": True}
        command = Command(
            name="release", description="Release", prompt="Release", metadata=metadata, replacements=replacements
        )

        result = transformer.command(command)

        assert result.metadata["release"] == "2.0"
        assert result.metadata["stable"] is True

    def test_should_preserve_non_string_types_in_command_metadata_when_transforming(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "enabled": True,
            "count": 42,
            "ratio": 3.14,
            "nothing": None,
        }
        command = Command(name="test", description="Test", prompt="Test", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["enabled"] is True
        assert result.metadata["count"] == 42
        assert result.metadata["ratio"] == 3.14
        assert result.metadata["nothing"] is None

    def test_should_transform_environment_variables_in_command_metadata_when_present(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("API_KEY", "secret123")
        monkeypatch.setenv("DB_HOST", "localhost")
        metadata = {
            "api_key": "{{env:API_KEY}}",
            "database": {
                "host": "{{env:DB_HOST}}",
            },
        }
        command = Command(name="connect", description="Connect", prompt="Connect", metadata=metadata)

        result = transformer.command(command)

        assert result.metadata["api_key"] == "secret123"
        assert result.metadata["database"]["host"] == "localhost"

    def test_should_preserve_replacements_in_command_when_transforming(
        self, transformer: PlaceholderTransformer
    ) -> None:
        replacements = {"version": ValueReplacement(value="1.0")}
        command = Command(name="test", description="test", prompt="Version: {{version}}", replacements=replacements)

        result = transformer.command(command)

        assert result.replacements == replacements


class TestRuleTransformation:
    def test_should_transform_rule_description_and_prompt(self, transformer: PlaceholderTransformer) -> None:
        rule = Rule(
            name="testing",
            description="Testing rules for {{project_name}}",
            prompt="Use {{var:framework}} for testing",
        )

        result = transformer.rule(rule)

        assert result.description == "Testing rules for my-project"
        assert result.prompt == "Use fastapi for testing"
        assert result.name == "testing"

    def test_should_apply_replacements_to_rule_description(self, transformer: PlaceholderTransformer) -> None:
        replacements = {"style": ValueReplacement(value="BDD")}
        rule = Rule(
            name="testing",
            description="Use {{style}} style",
            prompt="Test prompt",
            replacements=replacements,
        )

        result = transformer.rule(rule)

        assert result.description == "Use BDD style"

    def test_should_apply_replacements_to_rule_prompt(self, transformer: PlaceholderTransformer) -> None:
        replacements = {"framework": ValueReplacement(value="pytest")}
        rule = Rule(
            name="testing",
            description="Testing",
            prompt="Use {{framework}} for testing",
            replacements=replacements,
        )

        result = transformer.rule(rule)

        assert result.prompt == "Use pytest for testing"

    def test_should_preserve_rule_metadata_when_transforming(self, transformer: PlaceholderTransformer) -> None:
        metadata = {"category": "code-quality", "enabled": True}
        rule = Rule(name="quality", description="Quality rules", prompt="Maintain quality", metadata=metadata)

        result = transformer.rule(rule)

        assert result.metadata == metadata

    def test_should_transform_string_values_in_rule_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "project": "{{project_name}}",
            "framework": "{{var:framework}}",
            "enabled": True,
        }
        rule = Rule(name="testing", description="Testing", prompt="Test", metadata=metadata)

        result = transformer.rule(rule)

        assert result.metadata["project"] == "my-project"
        assert result.metadata["framework"] == "fastapi"
        assert result.metadata["enabled"] is True

    def test_should_transform_nested_structures_in_rule_metadata_when_present(
        self, transformer: PlaceholderTransformer
    ) -> None:
        metadata = {
            "config": {
                "project": "{{project_name}}",
                "settings": {
                    "language": "{{var:language}}",
                },
            },
            "tags": ["{{project_name}}", "rules"],
        }
        rule = Rule(name="config", description="Config", prompt="Config", metadata=metadata)

        result = transformer.rule(rule)

        assert result.metadata["config"]["project"] == "my-project"
        assert result.metadata["config"]["settings"]["language"] == "python"
        assert result.metadata["tags"] == ["my-project", "rules"]

    def test_should_apply_replacements_to_rule_metadata_when_present(self, transformer: PlaceholderTransformer) -> None:
        replacements = {"style": ValueReplacement(value="BDD")}
        metadata = {"testing_style": "{{style}}", "strict": False}
        rule = Rule(name="test", description="Test", prompt="Test", metadata=metadata, replacements=replacements)

        result = transformer.rule(rule)

        assert result.metadata["testing_style"] == "BDD"
        assert result.metadata["strict"] is False

    def test_should_transform_environment_variables_in_rule_metadata_when_present(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COVERAGE_THRESHOLD", "80")
        metadata = {
            "coverage": "{{env:COVERAGE_THRESHOLD}}",
        }
        rule = Rule(name="coverage", description="Coverage", prompt="Coverage", metadata=metadata)

        result = transformer.rule(rule)

        assert result.metadata["coverage"] == "80"


class TestMCPServerTransformation:
    def test_should_transform_stdio_mcp_server_command_and_args(self, transformer: PlaceholderTransformer) -> None:
        mcp_server = StdioMCPServer(
            name="test-server",
            type=TransportType.STDIO,
            command="{{project_dir}}/bin/server",
            args=["--project", "{{project_name}}", "--lang", "{{var:language}}"],
        )

        result = transformer.mcp_server(mcp_server)

        assert isinstance(result, StdioMCPServer)
        assert result.command == "/home/user/projects/my-project/bin/server"
        assert result.args == ["--project", "my-project", "--lang", "python"]

    def test_should_transform_stdio_mcp_server_environment_variables(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SECRET_KEY", "my-secret")
        mcp_server = StdioMCPServer(
            name="test-server",
            type=TransportType.STDIO,
            command="server",
            env={"PROJECT_NAME": "{{project_name}}", "SECRET": "{{env:SECRET_KEY}}"},
        )

        result = transformer.mcp_server(mcp_server)

        assert isinstance(result, StdioMCPServer)
        assert result.env == {"PROJECT_NAME": "my-project", "SECRET": "my-secret"}

    def test_should_transform_http_mcp_server_url(self, transformer: PlaceholderTransformer) -> None:
        mcp_server = HttpMCPServer(
            name="api-server",
            type=TransportType.HTTP,
            url="https://api.{{project_name}}.com",
        )

        result = transformer.mcp_server(mcp_server)

        assert isinstance(result, HttpMCPServer)
        assert result.url == "https://api.my-project.com"

    def test_should_transform_http_mcp_server_headers(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AUTH_TOKEN", "token123")
        mcp_server = HttpMCPServer(
            name="api-server",
            type=TransportType.HTTP,
            url="https://api.example.com",
            headers={"Authorization": "Bearer {{env:AUTH_TOKEN}}", "X-Project": "{{project_name}}"},
        )

        result = transformer.mcp_server(mcp_server)

        assert isinstance(result, HttpMCPServer)
        assert result.headers == {"Authorization": "Bearer token123", "X-Project": "my-project"}

    def test_should_preserve_mcp_server_name_and_type(self, transformer: PlaceholderTransformer) -> None:
        mcp_server = StdioMCPServer(
            name="my-server",
            type=TransportType.STDIO,
            command="server",
        )

        result = transformer.mcp_server(mcp_server)

        assert result.name == "my-server"
        assert result.type == TransportType.STDIO


class TestComplexScenarios:
    def test_should_handle_text_with_no_placeholders(self, transformer: PlaceholderTransformer) -> None:
        text = "This is plain text with no placeholders"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == text

    def test_should_handle_mixed_placeholder_types_in_single_text(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TOKEN", "xyz")
        replacements = {"version": ValueReplacement(value="3.0")}
        text = (
            "Project {{project_name}} using {{var:language}} v{{version}} in {{project_dir}} with token {{env:TOKEN}}"
        )
        command = Command(name="test", description="test", prompt=text, replacements=replacements)

        result = transformer.command(command)

        assert result.prompt == (
            "Project my-project using python v3.0 in /home/user/projects/my-project with token xyz"
        )

    def test_should_handle_nested_placeholder_syntax_literally(self, transformer: PlaceholderTransformer) -> None:
        text = "{{project_name}}_{{var:language}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "my-project_python"

    def test_should_handle_empty_prompt(self, transformer: PlaceholderTransformer) -> None:
        command = Command(name="test", description="test", prompt="")

        result = transformer.command(command)

        assert result.prompt == ""

    def test_should_process_all_placeholders_in_order(
        self, transformer: PlaceholderTransformer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MY_VAR", "{{project_name}}")
        text = "Value: {{env:MY_VAR}}"
        command = Command(name="test", description="test", prompt=text)

        result = transformer.command(command)

        assert result.prompt == "Value: {{project_name}}"
