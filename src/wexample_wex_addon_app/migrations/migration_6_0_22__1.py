from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_22__1(AbstractMigration):
    VERSION = "6.0.22"
    SEQ = 1
    DESCRIPTION = "Rename helper.proxy → sidecar.proxy in .wex/config.yml (helper concept renamed to sidecar)."

    @staticmethod
    def _config_path(context: MigrationContext) -> Path:
        return context.target_path / ".wex" / "config.yml"

    @staticmethod
    def _load_config(config_path: Path) -> dict | None:
        if not config_path.exists():
            return None
        with open(config_path) as fh:
            config = yaml.safe_load(fh) or {}
        return config if isinstance(config, dict) else None

    def apply(self, context: MigrationContext) -> None:
        config_path = self._config_path(context)
        config = self._load_config(config_path)
        if config is None:
            return

        helper = config.get("helper")
        if not isinstance(helper, dict):
            return

        config["sidecar"] = {**helper, **config.get("sidecar", {})}
        del config["helper"]

        with open(config_path, "w") as fh:
            yaml.safe_dump(config, fh, sort_keys=False)

    def rollback(self, context: MigrationContext) -> None:
        config_path = self._config_path(context)
        config = self._load_config(config_path)
        if config is None:
            return

        sidecar = config.get("sidecar")
        if not isinstance(sidecar, dict):
            return

        config["helper"] = {**sidecar, **config.get("helper", {})}
        del config["sidecar"]

        with open(config_path, "w") as fh:
            yaml.safe_dump(config, fh, sort_keys=False)
