from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6018(AbstractMigration):
    VERSION = "6.0.18"
    DESCRIPTION = (
        "Replace service.proxy: {} with helper.proxy: {} in .wex/config.yml "
        "for apps that depend on the proxy helper but do not host it. "
        "Apps where global.main_service == 'proxy' are left unchanged."
    )

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        service = config.get("service")
        if not isinstance(service, dict) or "proxy" not in service:
            return

        # Leave wex-proxy itself untouched — it actually hosts the proxy service
        if config.get("global", {}).get("main_service") == "proxy":
            return

        helper = config.get("helper")
        if not isinstance(helper, dict):
            helper = {}
            config["helper"] = helper

        helper.setdefault("proxy", {})
        del service["proxy"]
        if not service:
            del config["service"]

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False)

    def rollback(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        helper = config.get("helper")
        if not isinstance(helper, dict) or "proxy" not in helper:
            return

        service = config.get("service")
        if not isinstance(service, dict):
            service = {}
            config["service"] = service

        service.setdefault("proxy", {})
        del helper["proxy"]
        if not helper:
            del config["helper"]

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False)
