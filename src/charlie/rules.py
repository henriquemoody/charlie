"""Rules file generator for IDE-based agents."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import yaml

from charlie.schema import CharlieConfig, Command, RulesSection


def _format_command_reference(command: Command, command_prefix: str) -> str:
    """Format a command as a reference entry.

    Args:
        command: Command definition
        command_prefix: Command prefix

    Returns:
        Formatted command reference
    """
    lines = [
        f"### /{command_prefix}.{command.name}",
        "",
        f"**Description**: {command.description}",
        "",
        f"**Usage**: `/{command_prefix}.{command.name} <input>`",
        "",
        "**Scripts**:",
    ]

    if command.scripts.sh:
        lines.append(f"- Bash: `{command.scripts.sh}`")
    if command.scripts.ps:
        lines.append(f"- PowerShell: `{command.scripts.ps}`")

    lines.append("")  # Empty line after each command

    return "\n".join(lines)


def _extract_manual_additions(existing_content: str) -> str:
    """Extract manual additions from existing rules file.

    Args:
        existing_content: Existing file content

    Returns:
        Content between manual addition markers, or empty string
    """
    pattern = r"<!-- MANUAL ADDITIONS START -->(.*?)<!-- MANUAL ADDITIONS END -->"
    match = re.search(pattern, existing_content, re.DOTALL)

    if match:
        return match.group(1).strip()

    return ""


def _extract_frontmatter_fields(section: RulesSection) -> Dict[str, Any]:
    """Extract agent-specific frontmatter fields from a rules section.

    Args:
        section: Rules section with possible agent-specific fields

    Returns:
        Dictionary of frontmatter fields (excluding core Charlie fields)
    """
    # Get all fields
    section_dict = section.model_dump()

    # Remove core Charlie fields
    core_fields = {"title", "content", "order"}
    frontmatter = {k: v for k, v in section_dict.items() if k not in core_fields and v is not None}

    return frontmatter


def _format_frontmatter(frontmatter: Dict[str, Any]) -> str:
    """Format frontmatter as YAML for markdown files.

    Args:
        frontmatter: Dictionary of frontmatter fields

    Returns:
        Formatted YAML frontmatter string
    """
    if not frontmatter:
        return ""

    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n\n"


def _transform_path_placeholders(text: str, agent_spec: dict) -> str:
    """Replace path placeholders in text with agent-specific paths.

    Args:
        text: Text with potential path placeholders
        agent_spec: Agent specification from registry

    Returns:
        Text with resolved path placeholders
    """
    # Get the base agent directory (e.g., ".claude", ".cursor")
    agent_dir = Path(agent_spec.get("command_dir", "")).parent
    
    # Replace agent directory placeholder
    text = text.replace("{{agent_dir}}", str(agent_dir))
    
    # Replace commands directory placeholder
    commands_dir = agent_spec.get("command_dir", "")
    text = text.replace("{{commands_dir}}", commands_dir)
    
    # Replace rules directory placeholder (if rules_file is defined)
    if "rules_file" in agent_spec:
        rules_dir = str(Path(agent_spec["rules_file"]).parent)
        text = text.replace("{{rules_dir}}", rules_dir)
    else:
        # Fallback: use common pattern
        text = text.replace("{{rules_dir}}", str(agent_dir / "rules"))
    
    return text


def generate_rules_file(
    config: CharlieConfig,
    agent_name: str,
    agent_spec: dict,
    output_dir: str,
    mode: str = "merged",
) -> List[str]:
    """Generate rules file(s) for an agent.

    Args:
        config: Charlie configuration
        agent_name: Name of the agent
        agent_spec: Agent specification from registry
        output_dir: Base output directory
        mode: "merged" (single file) or "separate" (one file per section)

    Returns:
        List of paths to generated rules files
    """
    if mode == "separate" and config.rules and config.rules.sections:
        return _generate_separate_rules(config, agent_name, agent_spec, output_dir)
    else:
        return [_generate_merged_rules(config, agent_name, agent_spec, output_dir)]


def _generate_merged_rules(
    config: CharlieConfig, agent_name: str, agent_spec: dict, output_dir: str
) -> str:
    """Generate a single merged rules file with all sections.

    Args:
        config: Charlie configuration
        agent_name: Name of the agent
        agent_spec: Agent specification from registry
        output_dir: Base output directory

    Returns:
        Path to generated rules file
    """
    rules_path = Path(output_dir) / agent_spec["rules_file"]
    rules_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists to preserve manual additions
    manual_additions = ""
    if rules_path.exists():
        existing_content = rules_path.read_text(encoding="utf-8")
        manual_additions = _extract_manual_additions(existing_content)

    # Extract frontmatter from first section if exists (for merged mode)
    frontmatter = {}
    if config.rules and config.rules.sections:
        # Use frontmatter from first section with lowest order
        sorted_sections = sorted(
            config.rules.sections, key=lambda s: (s.order if s.order is not None else 999, s.title)
        )
        if sorted_sections:
            frontmatter = _extract_frontmatter_fields(sorted_sections[0])

    # Build rules content
    title = config.rules.title if config.rules else "Development Guidelines"
    current_date = datetime.now().strftime("%Y-%m-%d")

    content_parts = []

    # Add frontmatter if present
    if frontmatter:
        content_parts.append(_format_frontmatter(frontmatter))

    lines = [
        f"# {title}",
        "",
        f"Auto-generated by Charlie from configuration",
        f"Last updated: {current_date}",
        "",
    ]

    # Add custom sections if present
    if config.rules and config.rules.sections:
        sorted_sections = sorted(
            config.rules.sections, key=lambda s: (s.order if s.order is not None else 999, s.title)
        )
        for section in sorted_sections:
            lines.append(f"## {section.title}")
            lines.append("")
            # Transform path placeholders in content
            content = _transform_path_placeholders(section.content, agent_spec)
            lines.append(content)
            lines.append("")

    # Add commands list if configured
    if config.rules and config.rules.include_commands and config.commands:
        lines.append("## Available Commands")
        lines.append("")
        if config.project:
            for command in config.commands:
                lines.append(
                    f"- `/{config.project.command_prefix}.{command.name}` - {command.description}"
                )
            lines.append("")

            # Add detailed command reference
            lines.append("## Command Reference")
            lines.append("")
            for command in config.commands:
                lines.append(_format_command_reference(command, config.project.command_prefix))

    # Add manual additions section if preserve_manual is enabled
    if config.rules and config.rules.preserve_manual:
        lines.append("<!-- MANUAL ADDITIONS START -->")
        if manual_additions:
            lines.append(manual_additions)
        else:
            lines.append("<!-- Add your custom rules here - they will be preserved on regeneration -->")
        lines.append("<!-- MANUAL ADDITIONS END -->")

    content_parts.append("\n".join(lines))
    content = "".join(content_parts)

    # Write to file
    rules_path.write_text(content, encoding="utf-8")

    return str(rules_path)


def _generate_separate_rules(
    config: CharlieConfig, agent_name: str, agent_spec: dict, output_dir: str
) -> List[str]:
    """Generate separate rules files (one per section).

    Args:
        config: Charlie configuration
        agent_name: Name of the agent
        agent_spec: Agent specification from registry
        output_dir: Base output directory

    Returns:
        List of paths to generated rules files
    """
    generated_files = []

    if not config.rules or not config.rules.sections:
        return generated_files

    # Get base rules directory
    rules_file_path = Path(agent_spec["rules_file"])
    rules_dir = Path(output_dir) / rules_file_path.parent
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Sort sections by order
    sorted_sections = sorted(
        config.rules.sections, key=lambda s: (s.order if s.order is not None else 999, s.title)
    )

    for section in sorted_sections:
        # Generate filename from section title
        filename = section.title.lower().replace(" ", "-").replace("/", "-") + ".md"
        section_path = rules_dir / filename

        # Extract frontmatter for this section
        frontmatter = _extract_frontmatter_fields(section)

        content_parts = []

        # Add frontmatter if present
        if frontmatter:
            content_parts.append(_format_frontmatter(frontmatter))

        # Add section content
        # Transform path placeholders in content
        content_text = _transform_path_placeholders(section.content, agent_spec)
        lines = [
            f"# {section.title}",
            "",
            f"Auto-generated by Charlie from configuration",
            f"Last updated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            content_text,
        ]

        content_parts.append("\n".join(lines))
        content = "".join(content_parts)

        # Write file
        section_path.write_text(content, encoding="utf-8")
        generated_files.append(str(section_path))

    return generated_files


def generate_rules_for_agents(
    config: CharlieConfig,
    agents: List[str],
    agent_specs: dict,
    output_dir: str,
    mode: str = "merged",
) -> dict:
    """Generate rules files for multiple agents.

    Args:
        config: Charlie configuration
        agents: List of agent names
        agent_specs: Dictionary of agent specifications
        output_dir: Base output directory
        mode: "merged" (single file) or "separate" (one file per section)

    Returns:
        Dictionary mapping agent names to list of generated rules file paths
    """
    results = {}

    for agent_name in agents:
        if agent_name in agent_specs:
            agent_spec = agent_specs[agent_name]
            if "rules_file" in agent_spec:
                rules_paths = generate_rules_file(
                    config, agent_name, agent_spec, output_dir, mode=mode
                )
                results[agent_name] = rules_paths

    return results

