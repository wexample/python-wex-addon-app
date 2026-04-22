from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6020(AbstractMigration):
    VERSION = "6.0.20"
    DESCRIPTION = (
        "Rename apache.conf to web.conf inside .wex/apache/ and "
        ".wex/env/*/apache/ directories, and update references in docker-compose files."
    )

    def apply(self, context: MigrationContext) -> None:
        for apache_dir in self._apache_dirs(context.target_path):
            old = apache_dir / "apache.conf"
            new = apache_dir / "web.conf"
            if old.exists() and not new.exists():
                old.rename(new)

        for compose_file in self._docker_compose_files(context.target_path):
            content = compose_file.read_text()
            if "apache/apache.conf" in content:
                compose_file.write_text(
                    content.replace("apache/apache.conf", "apache/web.conf")
                )

    def rollback(self, context: MigrationContext) -> None:
        for apache_dir in self._apache_dirs(context.target_path):
            new = apache_dir / "web.conf"
            old = apache_dir / "apache.conf"
            if new.exists() and not old.exists():
                new.rename(old)

        for compose_file in self._docker_compose_files(context.target_path):
            content = compose_file.read_text()
            if "apache/web.conf" in content:
                compose_file.write_text(
                    content.replace("apache/web.conf", "apache/apache.conf")
                )

    def _apache_dirs(self, target_path: Path) -> list[Path]:
        dirs = [target_path / ".wex" / "apache"]
        env_dir = target_path / ".wex" / "env"
        if env_dir.is_dir():
            for d in env_dir.glob("*/apache"):
                if d.is_dir():
                    dirs.append(d)
        return dirs

    def _docker_compose_files(self, target_path: Path) -> list[Path]:
        return list((target_path / ".wex").rglob("docker-compose.yml"))
