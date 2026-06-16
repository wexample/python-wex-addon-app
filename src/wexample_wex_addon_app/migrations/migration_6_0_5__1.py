from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_5__1(AbstractMigration):
    VERSION = "6.0.5"
    SEQ = 1
    DESCRIPTION = "Move root .wex/config.<env>.yml files to .wex/env/<env>/config.yml"
    ENVIRONMENTS = ("prod", "dev", "local", "test")

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        env_base = wex_dir / "env"
        environments = self.ENVIRONMENTS

        for env_name in environments:
            source = wex_dir / f"config.{env_name}.yml"
            if not source.is_file():
                continue

            target_dir = env_base / env_name
            target_dir.mkdir(parents=True, exist_ok=True)
            source.rename(target_dir / "config.yml")

    def rollback(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        env_base = wex_dir / "env"
        environments = self.ENVIRONMENTS

        for env_name in environments:
            source = env_base / env_name / "config.yml"
            target = wex_dir / f"config.{env_name}.yml"
            if not source.is_file() or target.exists():
                continue

            source.rename(target)
