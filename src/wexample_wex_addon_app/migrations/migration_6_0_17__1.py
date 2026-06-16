from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext

# Keys dropped silently during step conversion
_STEP_KEYS_DROP = {"type", "context", "sync", "interpreter"}
# Keys that require a runtime warning when dropped
_STEP_KEYS_WARN = {"sync"}
# Keys copied verbatim from a v5 step dict to the v6 result
_STEP_PASSTHROUGH_KEYS = ("script", "file", "workdir", "ignore_error", "app_should_run")
# Top-level keys whose presence marks a file as v5 format
_V5_MARKERS = {"type", "help", "command", "properties"}


def _convert_properties(properties: list) -> list[dict]:
    """Convert v5 properties list to v6 decorators list."""
    decorators = []
    for prop in properties:
        if prop == "as_sudo":
            decorators.append({"name": "sudo"})
        elif prop == "app_webhook":
            decorators.append({"name": "webhook"})
        elif isinstance(prop, dict):
            name = prop.get("name")
            opts = prop.get("options", {})
            if name in ("attach", "alias"):
                decorators.append({"name": name, "args": opts})
    return decorators


def _convert_step(step, yaml_path: Path) -> dict:
    """Convert a single v5 step (str or dict) to a v6 step dict."""
    if isinstance(step, str):
        return {"runner": "bash", "script": step}

    result: dict = {}

    # title → name
    if "title" in step:
        result["name"] = step["title"]

    # variable (keep)
    if "variable" in step:
        result["variable"] = step["variable"]

    # Warn about unsupported keys before dropping them
    for key in _STEP_KEYS_WARN:
        if key in step:
            warnings.warn(
                f"{yaml_path}: step key '{key}' is not supported in wex 6 and was dropped.",
                stacklevel=2,
            )

    # Determine runner
    is_docker = "container_name" in step or step.get("context") == "container"
    interp = step.get("interpreter")
    is_python = isinstance(interp, list) and any("python" in s for s in interp)
    is_bash_file = step.get("type") == "bash-file"

    if is_docker:
        result["runner"] = "docker"
        result["service"] = step.get("container_name", step.get("service", ""))
    elif is_python:
        result["runner"] = "python"
    else:
        result["runner"] = "bash"

    for key in _STEP_PASSTHROUGH_KEYS:
        if key in step:
            result[key] = step[key]

    return result


def _convert_yaml(data: dict, yaml_path: Path) -> dict:
    """Convert a parsed v5 command dict to v6 format."""
    result: dict = {}

    # help → description
    if "help" in data:
        result["description"] = data["help"]
    elif "description" in data:
        result["description"] = data["description"]

    # properties → decorators
    decorators = _convert_properties(data.get("properties", []))
    if decorators:
        result["decorators"] = decorators

    # options: same format in v5 and v6
    if "options" in data:
        result["options"] = data["options"]

    # scripts: convert each step
    scripts = data.get("scripts", [])
    if scripts:
        result["scripts"] = [_convert_step(s, yaml_path) for s in scripts]

    # Dropped silently: type, command
    return result


def _rewrite_yaml_file(path: Path) -> None:
    import yaml

    raw = path.read_text()
    data = yaml.safe_load(raw) or {}

    # Skip if already looks like v6 (has 'description' or 'scripts' with runner keys,
    # and no v5-only top-level keys)
    if not any(k in data for k in _V5_MARKERS):
        return

    converted = _convert_yaml(data, path)
    path.write_text(
        yaml.dump(
            converted, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
    )


class Migration_6_0_17__1(AbstractMigration):
    VERSION = "6.0.17"
    SEQ = 1
    DESCRIPTION = (
        "Rename .wex/command/ → .wex/commands/ and rewrite YAML files from v5 to v6 format: "
        "help→description, properties→decorators, bare-string steps and docker/python step "
        "patterns converted to runner: syntax, title→name."
    )

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        old_dir = wex_dir / "command"
        new_dir = wex_dir / "commands"

        if not old_dir.is_dir():
            return

        if not context.dry_run:
            if new_dir.is_dir():
                # Destination exists — move contents of old_dir into new_dir (merge)
                for item in sorted(old_dir.rglob("*")):
                    rel = item.relative_to(old_dir)
                    dest = new_dir / rel
                    if item.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if not dest.exists():
                            item.rename(dest)
                # Remove old_dir tree (should be empty or contain only dirs now)
                import shutil

                shutil.rmtree(old_dir)
            else:
                old_dir.rename(new_dir)

        # Rewrite each YAML file in new_dir
        target = new_dir if not context.dry_run else old_dir
        for yaml_path in sorted(target.rglob("*.yml")):
            if not context.dry_run:
                _rewrite_yaml_file(yaml_path)

    def rollback(self, context: MigrationContext) -> None:
        # YAML content cannot be restored (conversion is lossy).
        # Only the directory rename is reversed.
        wex_dir = context.target_path / ".wex"
        new_dir = wex_dir / "commands"
        old_dir = wex_dir / "command"

        if new_dir.is_dir() and not old_dir.exists():
            if not context.dry_run:
                new_dir.rename(old_dir)
