from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6021(AbstractMigration):
    VERSION = "6.0.21"
    DESCRIPTION = (
        "Move Dockerfile.* files from .wex/docker/ into .wex/docker/images/, "
        "populate docker.images in .wex/config.yml from docker-compose build sections "
        "and Dockerfile FROM lines, and update dockerfile references in all docker-compose files."
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

        self._write_config_images(context.target_path, moved, images_dir)

    def rollback(self, context: MigrationContext) -> None:
        import yaml

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

        config_file = context.target_path / ".wex" / "config.yml"
        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}
            if "docker" in data and "images" in data["docker"]:
                del data["docker"]["images"]
                if not data["docker"]:
                    del data["docker"]
                with open(config_file, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    # ------------------------------------------------------------------

    def _write_config_images(
        self, target_path: Path, dockerfile_names: list[str], images_dir: Path
    ) -> None:
        import yaml

        config_file = target_path / ".wex" / "config.yml"
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        if data.get("docker", {}).get("images"):
            return

        tags = self._extract_tags_from_composes(target_path, dockerfile_names)
        app_name = data.get("global", {}).get("name", "app")
        images = {}

        for name in dockerfile_names:
            suffix = name.replace("Dockerfile.", "")
            tag = tags.get(name) or f"{app_name}-{suffix}:local"
            depends_on = self._detect_depends_on(
                images_dir / name, suffix, dockerfile_names
            )
            entry: dict = {
                "dockerfile": f".wex/docker/images/{name}",
                "tag": tag,
            }
            if depends_on:
                entry["depends_on"] = depends_on
            images[suffix] = entry

        data.setdefault("docker", {})["images"] = images
        with open(config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _extract_tags_from_composes(
        self, target_path: Path, dockerfile_names: list[str]
    ) -> dict[str, str]:
        import yaml

        tags: dict[str, str] = {}
        for compose_file in self._docker_compose_files(target_path):
            try:
                with open(compose_file) as f:
                    data = yaml.safe_load(f) or {}
            except Exception:
                continue
            for service in (data.get("services") or {}).values():
                if not isinstance(service, dict):
                    continue
                build = service.get("build")
                if not isinstance(build, dict):
                    continue
                dockerfile_val = build.get("dockerfile", "")
                image_tag = service.get("image")
                if not image_tag:
                    continue
                for name in dockerfile_names:
                    if name in dockerfile_val and name not in tags:
                        tags[name] = image_tag
        return tags

    def _detect_depends_on(
        self, dockerfile_path: Path, own_suffix: str, all_names: list[str]
    ) -> str | None:
        """Read the first FROM line and match its image name against known build suffixes."""
        if not dockerfile_path.exists():
            return None
        try:
            with open(dockerfile_path) as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.upper().startswith("FROM "):
                        parts = stripped.split()
                        if len(parts) < 2:
                            break
                        image_ref = parts[1]
                        image_name = image_ref.split(":")[0].split("/")[-1]
                        for name in all_names:
                            dep_suffix = name.replace("Dockerfile.", "")
                            if image_name == dep_suffix and dep_suffix != own_suffix:
                                return dep_suffix
                        break
        except Exception:
            pass
        return None

    def _docker_compose_files(self, target_path: Path) -> list[Path]:
        return list((target_path / ".wex").rglob("docker-compose.yml"))
