from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext

_REMOVABLE = ["__main__.py", "pyproject.toml", "requirements.txt"]


class Migration_6_0_16__1(AbstractMigration):
    VERSION = "6.0.16"
    SEQ = 1
    DESCRIPTION = (
        "Remove obsolete app_manager files (__main__.py, pyproject.toml, requirements.txt) "
        "from .wex/python/app_manager/ — applies to user apps and wex addon repos alike. "
        "Preserves app_workdir.py. Removes the directory if empty after cleanup."
    )

    def apply(self, context: MigrationContext) -> None:
        am_dir = context.target_path / ".wex" / "python" / "app_manager"
        if not am_dir.is_dir():
            return

        for name in _REMOVABLE:
            (am_dir / name).unlink(missing_ok=True)

        # Remove directory only if nothing remains (app_workdir.py may still be there)
        if next(am_dir.iterdir(), None) is None:
            am_dir.rmdir()

    def rollback(self, context: MigrationContext) -> None:
        # Deleted files cannot be restored; rollback is a no-op.
        pass
