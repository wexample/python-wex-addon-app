from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Rollback the last applied migration on the current app",
)
def app__migration__rollback(
    context: ExecutionContext, app_workdir: ManagedWorkdir
) -> None:
    from wexample_migration.workdir.mixin.with_migration_workdir_mixin import (
        WithMigrationWorkdirMixin,
    )

    if not isinstance(app_workdir, WithMigrationWorkdirMixin):
        context.io.error(
            "Current workdir does not support migrations. "
            "Mix WithMigrationWorkdirMixin into your workdir class and override get_migrations()."
        )
        return

    rolled_back = app_workdir.migration_rollback()

    if rolled_back:
        context.io.success(f"Rolled back: {rolled_back}")
    else:
        context.io.log("Nothing to rollback.")
