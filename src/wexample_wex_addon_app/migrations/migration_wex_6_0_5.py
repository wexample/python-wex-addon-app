from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex605(AbstractMigration):
    VERSION = "6.0.5"
    DESCRIPTION = "Move root .wex/config.<env>.yml files to .wex/env/<env>/config.yml"
    ENVIRONMENTS = ("prod", "dev", "local", "test")

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        for env_name in self.ENVIRONMENTS:
            source = wex_dir / f"config.{env_name}.yml"
            if not source.is_file():
                continue

            target_dir = wex_dir / "env" / env_name
            target_dir.mkdir(parents=True, exist_ok=True)
            source.rename(target_dir / "config.yml")

    def rollback(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        for env_name in self.ENVIRONMENTS:
            source = wex_dir / "env" / env_name / "config.yml"
            target = wex_dir / f"config.{env_name}.yml"
            if not source.is_file() or target.exists():
                continue

            source.rename(target)
