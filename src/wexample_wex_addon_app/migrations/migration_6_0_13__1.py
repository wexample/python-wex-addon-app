from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_13__1(AbstractMigration):
    VERSION = "6.0.13"
    SEQ = 1
    DESCRIPTION = "Ensure .wex/env/<env>/cron/default.cron exists as a file for php-derived services"
    PHP_SERVICES = {"php", "symfony"}
    DEFAULT_ENVS = ("local", "dev", "prod", "test")

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        config_path = wex_dir / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        service_config = config.get("service")
        if not isinstance(service_config, dict):
            return

        if not any(
            service_name in service_config for service_name in self.PHP_SERVICES
        ):
            return

        env_dir = wex_dir / "env"
        if env_dir.is_dir():
            env_names = [path.name for path in env_dir.iterdir() if path.is_dir()]
        else:
            env_names = []

        if not env_names:
            env_names = list(self.DEFAULT_ENVS)

        for env_name in env_names:
            cron_path = wex_dir / "env" / env_name / "cron" / "default.cron"

            if cron_path.is_dir():
                continue

            cron_path.parent.mkdir(parents=True, exist_ok=True)
            if not cron_path.exists():
                cron_path.write_text(
                    '#* * * * * echo "Hello world" > /var/log/cron.log 2>&1\n'
                )
