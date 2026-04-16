from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6019(AbstractMigration):
    VERSION = "6.0.19"
    DESCRIPTION = (
        "Auto-add helper.proxy: {} to any app that declares a domain, "
        "since domain-based routing always requires the reverse proxy. "
        "Apps where global.main_service == 'proxy' are skipped."
    )

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        # Skip the proxy helper app itself
        if config.get("global", {}).get("main_service") == "proxy":
            return

        # Only apply to apps that declare a domain
        has_domain = bool(config.get("domain") or config.get("domains"))
        if not has_domain:
            return

        # Already declared
        if isinstance(config.get("helper"), dict) and "proxy" in config["helper"]:
            return

        helper = config.get("helper")
        if not isinstance(helper, dict):
            helper = {}
            config["helper"] = helper

        helper["proxy"] = {}

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

        del helper["proxy"]
        if not helper:
            del config["helper"]

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False)
