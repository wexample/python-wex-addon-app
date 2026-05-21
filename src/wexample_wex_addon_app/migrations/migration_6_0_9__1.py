from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_9__1(AbstractMigration):
    VERSION = "6.0.9"
    SEQ = 1
    DESCRIPTION = (
        "Replace container_name prefixes from ${APP_NAME}_ to "
        "${APP_PROJECT_NAME}_ in docker-compose.yml files under .wex/"
    )

    @staticmethod
    def _find_compose_files(wex_dir: Path) -> list[Path]:
        return [
            path
            for path in wex_dir.rglob("docker-compose.yml")
            if "tmp" not in path.parts
        ]

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        for compose_path in self._find_compose_files(wex_dir):
            content = compose_path.read_text()
            updated = content.replace(
                "container_name: ${APP_NAME}_",
                "container_name: ${APP_PROJECT_NAME}_",
            )
            if updated != content:
                compose_path.write_text(updated)
