from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel
from rich.console import Console

from charlie.schema import CharlieConfig, Command, MCPServer, Rule

console = Console()

T = TypeVar("T", bound=BaseModel)


@dataclass
class MergeResult:
    config: CharlieConfig
    warnings: list[str] = field(default_factory=list)


def _get_item_name(item: Command | Rule | MCPServer) -> str:
    if isinstance(item, (Command, Rule)):
        return item.name

    return item.name


def _merge_named_list(
    base_items: list[T],
    new_items: list[T],
    item_type: str,
    source_name: str,
) -> tuple[list[T], list[str]]:
    warnings: list[str] = []
    result_map: dict[str, T] = {}

    for item in base_items:
        name = _get_item_name(item)  # type: ignore[arg-type]
        result_map[name] = item

    for item in new_items:
        name = _get_item_name(item)  # type: ignore[arg-type]
        if name in result_map:
            warnings.append(f"Overwriting {item_type} '{name}' from {source_name}")
        result_map[name] = item

    return list(result_map.values()), warnings


def _merge_variables(
    base_vars: dict[str, Any],
    new_vars: dict[str, Any],
    source_name: str,
) -> tuple[dict[str, Any], list[str]]:
    """Merge variable definitions."""
    warnings: list[str] = []
    result = dict(base_vars)

    for key, value in new_vars.items():
        if key in result:
            warnings.append(f"Overwriting variable '{key}' from {source_name}")
        result[key] = value

    return result, warnings


def _merge_ignore_patterns(base_patterns: list[str], new_patterns: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for pattern in base_patterns + new_patterns:
        if pattern not in seen:
            seen.add(pattern)
            result.append(pattern)

    return result


def merge_configs(base: CharlieConfig, overlay: CharlieConfig, source_name: str = "overlay") -> MergeResult:
    warnings: list[str] = []

    merged_commands, cmd_warnings = _merge_named_list(
        base.commands,
        overlay.commands,
        "command",
        source_name,
    )
    warnings.extend(cmd_warnings)

    merged_rules, rule_warnings = _merge_named_list(
        base.rules,
        overlay.rules,
        "rule",
        source_name,
    )
    warnings.extend(rule_warnings)

    merged_mcp_servers, mcp_warnings = _merge_named_list(
        list(base.mcp_servers),
        list(overlay.mcp_servers),
        "MCP server",
        source_name,
    )
    warnings.extend(mcp_warnings)

    merged_variables, var_warnings = _merge_variables(
        base.variables,
        overlay.variables,
        source_name,
    )
    warnings.extend(var_warnings)

    merged_ignore_patterns = _merge_ignore_patterns(
        base.ignore_patterns,
        overlay.ignore_patterns,
    )

    seen_assets: set[str] = set()
    merged_assets: list[str] = []
    for asset in base.assets + overlay.assets:
        if asset not in seen_assets:
            seen_assets.add(asset)
            merged_assets.append(asset)

    merged_project = overlay.project if overlay.project else base.project

    merged_config = CharlieConfig(
        version=overlay.version or base.version,
        project=merged_project,
        commands=merged_commands,
        rules=merged_rules,
        mcp_servers=merged_mcp_servers,
        variables=merged_variables,
        assets=merged_assets,
        ignore_patterns=merged_ignore_patterns,
    )

    return MergeResult(config=merged_config, warnings=warnings)


def merge_config_chain(configs: list[tuple[CharlieConfig, str]]) -> MergeResult:
    if not configs:
        raise ValueError("Cannot merge empty config list")

    all_warnings: list[str] = []
    result_config, _ = configs[0]

    for overlay_config, source_name in configs[1:]:
        merge_result = merge_configs(result_config, overlay_config, source_name)
        result_config = merge_result.config
        all_warnings.extend(merge_result.warnings)

    return MergeResult(config=result_config, warnings=all_warnings)
