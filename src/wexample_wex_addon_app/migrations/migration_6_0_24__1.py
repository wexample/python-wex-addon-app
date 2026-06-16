from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext

_RE_BARE = re.compile(r"\$(?!\{)([A-Za-z_][A-Za-z0-9_]*)")
_RE_BRACED = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _to_bare(text: str) -> str:
    return _RE_BRACED.sub(r"$\1", text)


def _to_braced(text: str) -> str:
    return _RE_BARE.sub(r"${\1}", text)


def _transform_scripts(scripts: list, fn) -> tuple[list, bool]:
    changed = False
    result = []
    for step in scripts:
        if isinstance(step, dict):
            new_step = None
            for key in ("script", "file"):
                if isinstance(step.get(key), str):
                    updated = fn(step[key])
                    if updated != step[key]:
                        if new_step is None:
                            new_step = dict(step)
                        new_step[key] = updated
                        changed = True
            if new_step is not None:
                step = new_step
        result.append(step)
    return result, changed


class Migration_6_0_24__1(AbstractMigration):
    VERSION = "6.0.24"
    SEQ = 1
    DESCRIPTION = (
        "Wrap bare shell variables ($VAR) in braces (${VAR}) in all script and file "
        "fields of .wex/commands/**/*.yml files."
    )

    def apply(self, context: MigrationContext) -> None:
        self._process(context, _to_braced)

    def rollback(self, context: MigrationContext) -> None:
        self._process(context, _to_bare)

    def _process(self, context: MigrationContext, fn) -> None:
        import yaml

        commands_dir = context.target_path / ".wex" / "commands"
        if not commands_dir.is_dir():
            return

        for yaml_path in sorted(commands_dir.rglob("*.yml")):
            raw = yaml_path.read_text()
            data = yaml.safe_load(raw) or {}

            if not isinstance(data, dict):
                continue

            scripts = data.get("scripts")
            if not isinstance(scripts, list):
                continue

            cleaned, changed = _transform_scripts(scripts, fn)
            if not changed or context.dry_run:
                continue

            data["scripts"] = cleaned
            yaml_path.write_text(
                yaml.dump(
                    data,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            )
