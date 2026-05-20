from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6027(AbstractMigration):
    VERSION = "6.0.27"
    DESCRIPTION = (
        "Run `app::config/suggest --apply` on the project to declare in "
        "config.yml → vars: every ${VAR} referenced by docker-compose."
    )

    def apply(self, context: MigrationContext) -> None:
        if context.dry_run:
            return

        kernel = context.extras.get("kernel")
        if kernel is None:
            return

        compose_path = context.target_path / ".wex" / "docker" / "docker-compose.yml"
        if not compose_path.exists():
            return

        from wexample_wex_addon_app.commands.config.suggest import app__config__suggest

        kernel.run_function(
            app__config__suggest,
            {"app_path": str(context.target_path), "apply": True},
        )
