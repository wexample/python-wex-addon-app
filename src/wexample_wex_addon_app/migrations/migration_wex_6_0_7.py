from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex607(AbstractMigration):
    VERSION = "6.0.7"
    DESCRIPTION = "Replace require_proxy: true with helper.proxy: {} in .wex/config.yml"

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        if config.get("require_proxy") is not True:
            return

        helper = config.get("helper")
        if not isinstance(helper, dict):
            helper = {}
            config["helper"] = helper

        helper.setdefault("proxy", {})
        config.pop("require_proxy", None)

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False)
