from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext

_WEX6_APP_MANAGER = Path(
    # @todo use absolute
    "/home/weeger/Desktop/WIP/WEB/WEXAMPLE/WEX/local/wex-6/.wex/bin/app-manager"
)


class MigrationWex600(AbstractMigration):
    VERSION = "6.0.0"
    DESCRIPTION = (
        "Migrate wex-5 app structure to wex-6: create .wex/bin/app-manager symlink"
    )

    def apply(self, context: MigrationContext) -> None:
        bin_dir = context.target_path / ".wex" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        symlink = bin_dir / "app-manager"
        if symlink.exists() or symlink.is_symlink():
            symlink.unlink()

        os.symlink(_WEX6_APP_MANAGER, symlink)

    def guess_version(self, context: MigrationContext) -> bool:
        # A wex-5 app has wex.version starting with "5." in config.yml
        # and no .wex/bin/ directory yet
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return False

        import yaml

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        wex_version = data.get("wex", {}).get("version") or data.get("global", {}).get(
            "version"
        )

        return isinstance(wex_version, str) and wex_version.startswith("5.")

    def rollback(self, context: MigrationContext) -> None:
        symlink = context.target_path / ".wex" / "bin" / "app-manager"
        if symlink.is_symlink():
            symlink.unlink()

        bin_dir = context.target_path / ".wex" / "bin"
        try:
            bin_dir.rmdir()
        except OSError:
            pass
