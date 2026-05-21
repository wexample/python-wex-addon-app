from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_22__1(AbstractMigration):
    VERSION = "6.0.22"
    SEQ = 1
    DESCRIPTION = "Rename helper.proxy → sidecar.proxy in .wex/config.yml (helper concept renamed to sidecar)."

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            return

        helper = config.get("helper")
        if not isinstance(helper, dict):
            return

        sidecar = config.setdefault("sidecar", {})
        for key, value in helper.items():
            sidecar.setdefault(key, value)
        del config["helper"]

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

        sidecar = config.get("sidecar")
        if not isinstance(sidecar, dict):
            return

        helper = config.setdefault("helper", {})
        for key, value in sidecar.items():
            helper.setdefault(key, value)
        del config["sidecar"]

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, sort_keys=False)
