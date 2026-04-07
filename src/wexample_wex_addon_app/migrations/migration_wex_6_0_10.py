from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex610(AbstractMigration):
    VERSION = "6.0.10"
    DESCRIPTION = (
        "Ensure global.type=app and move docker.main_db_container "
        "to docker.db.main in .wex/config.yml"
    )

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        changed = False

        global_config = config.get("global")
        if not isinstance(global_config, dict):
            global_config = {}
            config["global"] = global_config
            changed = True

        if global_config.get("type") != "app":
            global_config["type"] = "app"
            changed = True

        docker_config = config.get("docker")
        legacy_main_db = None
        if isinstance(docker_config, dict):
            legacy_main_db = docker_config.pop("main_db_container", None)
            if legacy_main_db is not None:
                changed = True
            if not docker_config:
                config.pop("docker", None)
                changed = True

        docker_config = config.get("docker")
        if not isinstance(docker_config, dict):
            docker_config = {}
            config["docker"] = docker_config
            changed = True

        db_config = docker_config.get("db")
        if not isinstance(db_config, dict):
            db_config = {}
            docker_config["db"] = db_config
            changed = True

        if legacy_main_db and db_config.get("main") != legacy_main_db:
            db_config["main"] = legacy_main_db
            changed = True

        if changed:
            with open(config_path, "w") as file:
                yaml.safe_dump(config, file, sort_keys=False)
