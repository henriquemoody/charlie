"""Command-line interface for charlie."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from charlie.agents.registry import get_agent_info, list_supported_agents
from charlie.parser import ConfigParseError, find_config_file, parse_config
from charlie.transpiler import CommandTranspiler

app = typer.Typer(
    name="charlie",
    help="Universal command transpiler for AI agents, MCP servers, and rules",
    add_completion=False,
)
console = Console()


def _resolve_config_file(config_path: str | None) -> Path:
    """Resolve configuration file path.

    Args:
        config_path: Explicit path or None for auto-detection

    Returns:
        Resolved path to configuration file or directory

    Raises:
        FileNotFoundError: If explicitly provided config file doesn't exist
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return path

    # Auto-detect charlie.yaml, .charlie.yaml, or .charlie/
    found = find_config_file()
    if found:
        return found

    # No config found - use current directory (will create default config)
    return Path.cwd()


@app.command()
def setup(
    agent: str = typer.Argument(..., help="Agent name to generate configuration for"),
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: auto-detect charlie.yaml)",
    ),
    mcp: bool = typer.Option(False, "--mcp", help="Generate MCP server configuration"),
    rules: bool = typer.Option(False, "--rules", help="Generate rules files"),
    rules_mode: str = typer.Option(
        "merged",
        "--rules-mode",
        help="Rules generation mode: 'merged' (single file) or 'separate' (one file per section)",
    ),
    output: str = typer.Option(".", "--output", "-o", help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Setup agent-specific configurations from YAML definition.

    Examples:

        # Auto-detect charlie.yaml and setup for Claude
        charlie setup claude

        # Explicit config file
        charlie setup gemini --config my-config.yaml

        # Setup with rules
        charlie setup cursor --rules

        # Setup with MCP and rules
        charlie setup claude --mcp --rules

        # Custom output directory
        charlie setup cursor --output ./build
    """
    try:
        # Resolve config file
        config_file = _resolve_config_file(config_path)

        console.print(f"[cyan]Using configuration:[/cyan] {config_file}")

        # Initialize transpiler
        transpiler = CommandTranspiler(str(config_file))

        # Generate
        console.print(f"\n[bold]Setting up {agent}...[/bold]")

        results = transpiler.generate(
            agent=agent,
            mcp=mcp,
            rules=rules,
            rules_mode=rules_mode,
            output_dir=output,
        )

        # Display results
        console.print(f"\n[green]✓ Setup complete for {agent}![/green]\n")

        for target_name, files in results.items():
            console.print(f"[cyan]{target_name}:[/cyan]")
            for filepath in files:
                if verbose:
                    console.print(f"  • {filepath}")
                else:
                    # Show relative path
                    try:
                        rel_path = Path(filepath).relative_to(Path(output).resolve())
                    except ValueError:
                        # If filepath is not relative to output, show absolute
                        rel_path = Path(filepath)
                    console.print(f"  • {rel_path}")

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
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def validate(
    config_path: str | None = typer.Argument(
        None, help="Path to configuration file (default: auto-detect charlie.yaml)"
    ),
) -> None:
    """Validate YAML configuration file.

    Examples:

        # Validate charlie.yaml in current directory
        charlie validate

        # Validate specific file
        charlie validate my-config.yaml
    """
    try:
        config_file = _resolve_config_file(config_path)

        console.print(f"[cyan]Validating:[/cyan] {config_file}")

        # Parse will raise error if invalid
        config = parse_config(config_file)

        console.print("\n[green]✓ Configuration is valid![/green]\n")
        project_name = config.project.name if config.project else "unknown"
        command_prefix = config.project.command_prefix if config.project else None
        console.print(f"  Project: {project_name}")
        console.print(f"  Command prefix: {command_prefix or '(none)'}")
        console.print(f"  Commands: {len(config.commands)}")
        console.print(f"  MCP servers: {len(config.mcp_servers)}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Validation Failed:[/red]\n{e}")
        raise typer.Exit(1)


@app.command("list-agents")
def list_agents() -> None:
    """List all supported AI agents.

    Examples:

        charlie list-agents
    """
    agents = list_supported_agents()

    console.print("\n[bold]Supported AI Agents:[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Agent Name", style="cyan")
    table.add_column("Display Name")
    table.add_column("Format")
    table.add_column("Command Directory")

    for agent_name in agents:
        info = get_agent_info(agent_name)
        if info:
            table.add_row(
                agent_name, info["name"], info["file_format"], info["command_dir"]
            )

    console.print(table)
    console.print(f"\n[dim]Total: {len(agents)} agents[/dim]\n")


@app.command()
def info(
    agent: str = typer.Argument(..., help="Agent name to show information for"),
) -> None:
    """Show detailed information about an agent.

    Examples:

        charlie info claude
        charlie info gemini
    """
    agent_info = get_agent_info(agent)

    if not agent_info:
        console.print(f"[red]Error:[/red] Unknown agent '{agent}'")
        console.print(
            "\n[dim]Use 'charlie list-agents' to see available agents[/dim]"
        )
        raise typer.Exit(1)

    # Create info panel
    info_lines = [
        f"[bold]Agent:[/bold] {agent_info['name']}",
        "",
        f"[cyan]Format:[/cyan] {agent_info['file_format']}",
        f"[cyan]Command directory:[/cyan] {agent_info['command_dir']}",
        f"[cyan]File extension:[/cyan] {agent_info['file_extension']}",
        f"[cyan]Argument placeholder:[/cyan] {agent_info['arg_placeholder']}",
        f"[cyan]Rules file:[/cyan] {agent_info['rules_file']}",
    ]

    panel = Panel(
        "\n".join(info_lines), title=f"[bold]{agent}[/bold]", border_style="cyan"
    )

    console.print()
    console.print(panel)
    console.print()


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()

