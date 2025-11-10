from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from charlie.agents.registry import AgentSpecRegistry
from charlie.config_reader import ConfigParseError, find_config_file, parse_config

app = typer.Typer(
    name="charlie",
    help="Universal command transpiler for AI agents, MCP servers, and rules",
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
def setup(
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
        "merged",
        "--rules-mode",
        help="Rules generation mode: 'merged' (single file) or 'separate' (one file per section)",
    ),
    output_dir_path: str = typer.Option(".", "--output", "-o", help="Output directory"),
    verbose_output: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    try:
        resolved_config_file = _resolve_config_file(config_path)

        console.print(f"[cyan]Using configuration:[/cyan] {resolved_config_file}")

        charlie_config = parse_config(str(resolved_config_file))

        resolved_path = resolved_config_file.resolve()
        if resolved_path.is_dir():
            if resolved_path.name == ".charlie":
                root_dir = str(resolved_path.parent)
            else:
                root_dir = str(resolved_path)
        else:
            root_dir = str(resolved_path.parent)

        agent_registry = AgentSpecRegistry()
        agent_spec = agent_registry.get(agent_name)

        if charlie_config.project is None:
            from charlie.schema import ProjectConfig

            charlie_config.project = ProjectConfig(name="unknown", command_prefix=None)

        from charlie.configurator import AgentConfiguratorFactory
        from charlie.tracker import Tracker

        tracker = Tracker()
        configurator = AgentConfiguratorFactory.create(
            agent_spec=agent_spec,
            project_config=charlie_config.project,
            tracker=tracker,
            root_dir=root_dir,
        )

        console.print(f"\n[bold]Setting up {agent_name}...[/bold]")

        generation_results: dict[str, list[str]] = {}

        if not no_commands:
            generated_commands = configurator.commands(charlie_config.commands, output_dir_path)
            generation_results["commands"] = generated_commands

        if not no_mcp and charlie_config.mcp_servers:
            mcp_file = configurator.mcp_servers(charlie_config, output_dir_path)
            generation_results["mcp"] = [mcp_file]

        if not no_rules:
            rules_files = configurator.rules(charlie_config, output_dir_path, rules_generation_mode)
            generation_results["rules"] = rules_files

        assets_files = configurator.assets(output_dir_path)
        if assets_files:
            generation_results["assets"] = assets_files

        console.print(f"\n[green]✓ Setup complete for {agent_name}![/green]\n")

        for target_category, generated_files in generation_results.items():
            console.print(f"[cyan]{target_category}:[/cyan]")
            for file_path in generated_files:
                if verbose_output:
                    console.print(f"  • {file_path}")
                else:
                    try:
                        relative_path = Path(file_path).relative_to(Path(output_dir_path).resolve())
                    except ValueError:
                        relative_path = Path(file_path)
                    console.print(f"  • {relative_path}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Configuration Error:[/red]\n{e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
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
        command_prefix = validated_config.project.command_prefix if validated_config.project else None
        console.print(f"  Project: {project_name}")
        console.print(f"  Command prefix: {command_prefix or '(none)'}")
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
    agent_registry = AgentSpecRegistry()
    supported_agent_names = agent_registry.list()

    console.print("\n[bold]Supported AI Agents:[/bold]\n")

    agents_table = Table(show_header=True, header_style="bold cyan")
    agents_table.add_column("Agent Name", style="cyan")
    agents_table.add_column("Display Name")
    agents_table.add_column("Format")
    agents_table.add_column("Command Directory")

    for agent_name in supported_agent_names:
        agent_specification = agent_registry.get(agent_name)
        agents_table.add_row(
            agent_name, agent_specification.name, agent_specification.file_format, agent_specification.command_dir
        )

    console.print(agents_table)
    console.print(f"\n[dim]Total: {len(supported_agent_names)} agents[/dim]\n")


@app.command()
def info(
    agent_name: str = typer.Argument(..., help="Agent name to show information for"),
) -> None:
    try:
        agent_registry = AgentSpecRegistry()
        agent_specification = agent_registry.get(agent_name)
    except ValueError:
        console.print(f"[red]Error:[/red] Unknown agent '{agent_name}'")
        console.print("\n[dim]Use 'charlie list-agents' to see available agents[/dim]")
        raise typer.Exit(1)

    agent_info_lines = [
        f"[bold]Agent:[/bold] {agent_specification.name}",
        "",
        f"[cyan]Format:[/cyan] {agent_specification.file_format}",
        f"[cyan]Command directory:[/cyan] {agent_specification.command_dir}",
        f"[cyan]Command extension:[/cyan] {agent_specification.command_extension}",
        f"[cyan]Rules extension:[/cyan] {agent_specification.rules_extension}",
        f"[cyan]Argument placeholder:[/cyan] {agent_specification.arg_placeholder}",
        f"[cyan]Rules file:[/cyan] {agent_specification.rules_file}",
    ]

    info_panel = Panel("\n".join(agent_info_lines), title=f"[bold]{agent_name}[/bold]", border_style="cyan")

    console.print()
    console.print(info_panel)
    console.print()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
