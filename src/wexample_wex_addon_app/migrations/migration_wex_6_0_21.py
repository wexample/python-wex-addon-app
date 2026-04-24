from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6021(AbstractMigration):
    VERSION = "6.0.21"
    DESCRIPTION = (
        "Move Dockerfile.* files from .wex/docker/ into .wex/docker/images/ "
        "and update dockerfile references in all docker-compose files."
    )

    def apply(self, context: MigrationContext) -> None:
        docker_dir = context.target_path / ".wex" / "docker"
        images_dir = docker_dir / "images"

        dockerfiles = list(docker_dir.glob("Dockerfile.*")) if docker_dir.is_dir() else []
        if not dockerfiles:
            return

        images_dir.mkdir(exist_ok=True)

        moved = []
        for dockerfile in dockerfiles:
            dest = images_dir / dockerfile.name
            if not dest.exists():
                dockerfile.rename(dest)
                moved.append(dockerfile.name)

        if not moved:
            return

        for compose_file in self._docker_compose_files(context.target_path):
            content = compose_file.read_text()
            updated = content
            for name in moved:
                updated = updated.replace(
                    f"docker/{name}",
                    f"docker/images/{name}",
                )
            if updated != content:
                compose_file.write_text(updated)

    def rollback(self, context: MigrationContext) -> None:
        docker_dir = context.target_path / ".wex" / "docker"
        images_dir = docker_dir / "images"

        if not images_dir.is_dir():
            return

        dockerfiles = list(images_dir.glob("Dockerfile.*"))
        moved = []
        for dockerfile in dockerfiles:
            dest = docker_dir / dockerfile.name
            if not dest.exists():
                dockerfile.rename(dest)
                moved.append(dockerfile.name)

        for compose_file in self._docker_compose_files(context.target_path):
            content = compose_file.read_text()
            updated = content
            for name in moved:
                updated = updated.replace(
                    f"docker/images/{name}",
                    f"docker/{name}",
                )
            if updated != content:
                compose_file.write_text(updated)

        if images_dir.is_dir() and not list(images_dir.iterdir()):
            images_dir.rmdir()

    def _docker_compose_files(self, target_path: Path) -> list[Path]:
        return list((target_path / ".wex").rglob("docker-compose.yml"))
