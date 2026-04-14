from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6014(AbstractMigration):
    VERSION = "6.0.14"
    DESCRIPTION = "Replace legacy RUNTIME_BRANCH placeholders with APP_BRANCH in app docker-compose files"

    @staticmethod
    def _iter_compose_files(context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        base_docker_dir = wex_dir / "docker"
        if base_docker_dir.is_dir():
            yield from sorted(base_docker_dir.glob("docker-compose*.yml"))

        env_dir = wex_dir / "env"
        if not env_dir.is_dir():
            return

        for env_path in sorted(path for path in env_dir.iterdir() if path.is_dir()):
            docker_dir = env_path / "docker"
            if docker_dir.is_dir():
                yield from sorted(docker_dir.glob("docker-compose*.yml"))

    def apply(self, context: MigrationContext) -> None:
        for compose_path in self._iter_compose_files(context):
            content = compose_path.read_text()
            updated = content.replace("RUNTIME_BRANCH", "APP_BRANCH")
            if updated != content:
                compose_path.write_text(updated)

    def rollback(self, context: MigrationContext) -> None:
        for compose_path in self._iter_compose_files(context):
            content = compose_path.read_text()
            updated = content.replace("APP_BRANCH", "RUNTIME_BRANCH")
            if updated != content:
                compose_path.write_text(updated)
