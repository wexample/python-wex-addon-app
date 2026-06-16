from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_19__1(AbstractMigration):
    VERSION = "6.0.19"
    SEQ = 1
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

        # Only apply to apps that declare a domain (root config or any env config)
        has_domain = config.get("domain") or config.get("domains")
        if not has_domain:
            env_dir = context.target_path / ".wex" / "env"
            if env_dir.is_dir():
                for env_config_path in env_dir.glob("*/config.yml"):
                    with open(env_config_path) as f:
                        env_config = yaml.safe_load(f) or {}
                    if isinstance(env_config, dict) and (
                        env_config.get("domain") or env_config.get("domains")
                    ):
                        has_domain = True
                        break
        if not has_domain:
            return

        helper = config.get("helper")
        # Already declared
        if isinstance(helper, dict) and "proxy" in helper:
            return

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
