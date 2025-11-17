from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from charlie.agent_registry import AgentRegistry
from charlie.config_reader import ConfigParseError, find_config_file, parse_config
from charlie.configurators.agent_configurator_factory import AgentConfiguratorFactory
from charlie.enums import RuleMode
from charlie.placeholder_transformer import PlaceholderTransformer
from charlie.tracker import Tracker
from charlie.variable_collector import VariableCollector

app = typer.Typer(
    name="charlie",
    help="Universal Agent Config Generator",
    add_completion=False,
)
console = Console()


def _resolve_config_file(config_path: str | None) -> Path:
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return path

    found = find_config_file()
    if found:
        return found

    return Path.cwd()


@app.command()
def generate(
    agent_name: str = typer.Argument(..., help="Agent name to generate configuration for"),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: auto-detect charlie.yaml)",
    ),
    no_commands: bool = typer.Option(False, "--no-commands", help="Skip command file generation"),
    no_mcp: bool = typer.Option(False, "--no-mcp", help="Skip MCP server configuration"),
    no_rules: bool = typer.Option(False, "--no-rules", help="Skip rules file generation"),
    rules_generation_mode: str = typer.Option(
        "separate",
        "--rules-mode",
        help="Rules generation mode: 'separate' (single file) or 'separate' (one file per section)",
    ),
    output_dir_path: str = typer.Option(".", "--output", "-o", help="Output directory"),
    verbose_output: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    try:
        resolved_config_file = _resolve_config_file(config_path)

        console.print(f"[cyan]Using configuration:[/cyan] {resolved_config_file}")

        charlie_config = parse_config(str(resolved_config_file))

        agent_registry = AgentRegistry()
        agent = agent_registry.get(agent_name)

        tracker = Tracker()
        configurator = AgentConfiguratorFactory.create(
            agent=agent,
            project=charlie_config.project,
            tracker=tracker,
        )

        variable_collector = VariableCollector()
        variables = variable_collector.collect(charlie_config.variables)

        transformer = PlaceholderTransformer(
            agent=agent,
            variables=variables,
            project=charlie_config.project,
        )

        console.print(f"\n[bold]Setting up {agent.name}...[/bold]\n")

        if not no_commands:
            configurator.commands([transformer.command(command) for command in charlie_config.commands])

        if not no_mcp and charlie_config.mcp_servers:
            configurator.mcp_servers([transformer.mcp_server(mcp_server) for mcp_server in charlie_config.mcp_servers])

        if not no_rules:
            configurator.rules(
                [transformer.rule(rule) for rule in charlie_config.rules],
                RuleMode(rules_generation_mode),
            )

        if charlie_config.assets:
            configurator.assets(charlie_config.assets)

        if charlie_config.ignore_patterns:
            configurator.ignore_file(charlie_config.ignore_patterns)

        for record in tracker.records:
            console.print(f" • {record['event']}")

        console.print(f"\n[green]✓ Setup complete for {agent_name}![/green]\n")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Configuration Error:[/red]\n{e}")
        # pint(e)
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        print(e)
        console.print(f"[red]Unexpected Error:[/red] {e}")
        if verbose_output:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def validate(
    config_path: str | None = typer.Argument(
        None, help="Path to configuration file (default: auto-detect charlie.yaml)"
    ),
) -> None:
    try:
        resolved_config_file = _resolve_config_file(config_path)

        console.print(f"[cyan]Validating:[/cyan] {resolved_config_file}")

        validated_config = parse_config(resolved_config_file)

        console.print("\n[green]✓ Configuration is valid![/green]\n")
        project_name = validated_config.project.name if validated_config.project else "unknown"
        namespace = validated_config.project.namespace if validated_config.project else None
        console.print(f"  Project: {project_name}")
        console.print(f"  Namespace: {namespace or '(none)'}")
        console.print(f"  Commands: {len(validated_config.commands)}")
        console.print(f"  MCP servers: {len(validated_config.mcp_servers)}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Validation Failed:[/red]\n{e}")
        raise typer.Exit(1)


@app.command("list-agents")
def list_agents() -> None:
    agent_registry = AgentRegistry()
    supported_agent_names = agent_registry.list()

    console.print("\n[bold]Supported AI Agents:[/bold]\n")

    agents_table = Table(show_header=True, header_style="bold cyan")
    agents_table.add_column("Shortname", style="cyan")
    agents_table.add_column("Display Name")

    for agent_name in supported_agent_names:
        agent = agent_registry.get(agent_name)
        agents_table.add_row(agent_name, agent.name)

    console.print(agents_table)
    console.print(f"\n[dim]Total: {len(supported_agent_names)} agents[/dim]\n")


@app.command()
def info(
    agent_name: str = typer.Argument(..., help="Agent name to show information for"),
) -> None:
    try:
        agent_registry = AgentRegistry()
        agent = agent_registry.get(agent_name)
    except ValueError:
        console.print(f"[red]Error:[/red] Unknown agent '{agent_name}'")
        console.print("\n[dim]Use 'charlie list-agents' to see available agents[/dim]")
        raise typer.Exit(1)

    # Display all fields from Agent as a table
    agent_info_table = Table(show_header=True, header_style="bold cyan")
    agent_info_table.add_column("Field", style="cyan")
    agent_info_table.add_column("Value")

    for key, value in agent.__dict__.items():
        agent_info_table.add_row(key, str(value))

    console.print(agent_info_table)
    console.print()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
