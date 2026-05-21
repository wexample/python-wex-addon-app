from __future__ import annotations

import stat
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_0__1(AbstractMigration):
    VERSION = "6.0.0"
    SEQ = 1
    DESCRIPTION = "Migrate wex-5 app structure to wex-6: write .wex/bin/app-manager from resources"

    def apply(self, context: MigrationContext) -> None:
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        bin_dir = context.target_path / ".wex" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        target = bin_dir / "app-manager"

        # Remove broken symlink or stale file before writing
        if target.is_symlink() or target.exists():
            target.unlink()

        source = AppAddonManager.get_shell_manager_path()
        target.write_text(source.read_text())
        target.chmod(
            target.stat().st_mode
            | stat.S_IRWXU
            | stat.S_IRGRP
            | stat.S_IXGRP
            | stat.S_IROTH
            | stat.S_IXOTH
        )

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
        target = context.target_path / ".wex" / "bin" / "app-manager"
        if target.exists() and not target.is_symlink():
            target.unlink()

        bin_dir = context.target_path / ".wex" / "bin"
        try:
            bin_dir.rmdir()
        except OSError:
            pass
