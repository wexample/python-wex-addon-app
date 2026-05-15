from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6026(AbstractMigration):
    VERSION = "6.0.26"
    DESCRIPTION = (
        "Copy entries from .wex/.env into .wex/local/env.yml. "
        "The .env file is preserved as legacy and no longer consumed."
    )

    def apply(self, context: MigrationContext) -> None:
        from dotenv import dotenv_values

        env_path = context.target_path / ".wex" / ".env"
        yaml_path = context.target_path / ".wex" / "local" / "env.yml"

        if not env_path.exists():
            return

        env_values = dotenv_values(env_path)
        if not env_values:
            return

        yaml_values: dict = {}
        if yaml_path.exists():
            with open(yaml_path) as f:
                loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                yaml_values = loaded

        # YAML wins on conflicts (new source of truth).
        merged = dict(yaml_values)
        for key, value in env_values.items():
            if value is None:
                continue
            merged.setdefault(key, value)

        if merged == yaml_values:
            return

        if context.dry_run:
            return

        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w") as f:
            yaml.safe_dump(merged, f, sort_keys=False)

    def rollback(self, context: MigrationContext) -> None:
        # No rollback: .env is preserved intact, so reverting just means
        # deleting the YAML manually if needed. We cannot safely identify
        # which YAML keys were added by this migration vs by later edits.
        return
