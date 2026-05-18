from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6023(AbstractMigration):
    VERSION = "6.0.23"
    DESCRIPTION = (
        "Remove empty script steps (entries with a 'runner' key but no 'script', "
        "'file', or 'command' key) from all .wex/commands/**/*.yml files."
    )

    def apply(self, context: MigrationContext) -> None:
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

            cleaned = [
                step
                for step in scripts
                if not isinstance(step, dict)
                or any(k in step for k in ("script", "file", "command"))
            ]

            if len(cleaned) == len(scripts):
                continue

            data["scripts"] = cleaned
            if not context.dry_run:
                yaml_path.write_text(
                    yaml.dump(
                        data,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
                )

    def rollback(self, context: MigrationContext) -> None:
        # Lossy migration: removed steps cannot be restored.
        pass
