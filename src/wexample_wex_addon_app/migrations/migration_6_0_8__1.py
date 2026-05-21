from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_8__1(AbstractMigration):
    VERSION = "6.0.8"
    SEQ = 1
    DESCRIPTION = (
        "Add service.letsencrypt to .wex/config.yml when at least one "
        ".wex/env/*/config.yml defines a non-empty domains list"
    )

    @staticmethod
    def _has_env_domains(wex_dir) -> bool:
        env_dir = wex_dir / "env"
        if not env_dir.exists():
            return False

        for config_path in env_dir.glob("*/config.yml"):
            with open(config_path) as file:
                env_config = yaml.safe_load(file) or {}

            if not isinstance(env_config, dict):
                continue

            domains = env_config.get("domains")
            if isinstance(domains, list) and len(domains) > 0:
                return True

        return False

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        main_config_path = wex_dir / "config.yml"
        if not main_config_path.exists():
            return

        if not self._has_env_domains(wex_dir):
            return

        with open(main_config_path) as file:
            main_config = yaml.safe_load(file) or {}

        if not isinstance(main_config, dict):
            return

        service = main_config.get("service")
        if not isinstance(service, dict):
            service = {}
            main_config["service"] = service

        if "letsencrypt" in service:
            return

        service["letsencrypt"] = {}

        with open(main_config_path, "w") as file:
            yaml.safe_dump(main_config, file, sort_keys=False)
