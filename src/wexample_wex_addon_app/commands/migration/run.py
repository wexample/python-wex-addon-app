from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    "dry_run",
    type=bool,
    short_name="d",
    required=False,
    is_flag=True,
    default=False,
    description="Simulate migrations without applying any changes",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Apply pending migrations to the current app",
)
def app__migration__run(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    dry_run: bool = False,
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

    if dry_run:
        context.io.log("Dry run — no changes will be written.")

    applied = app_workdir.migration_run(
        dry_run=dry_run,
        extras={"workdir": app_workdir, "kernel": context.kernel},
    )

    if applied:
        label = "Would apply" if dry_run else "Applied"
        context.io.success(f"{label}: {', '.join(applied)}")
    else:
        context.io.log("No pending migrations.")
