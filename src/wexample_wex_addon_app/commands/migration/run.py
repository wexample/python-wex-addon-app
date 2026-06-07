from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

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
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DB,
        DomainTag.MIGRATION,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__migration__run(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    dry_run: bool = False,
):
    from wexample_app.response.failure_response import FailureResponse
    from wexample_app.response.success_response import SuccessResponse
    from wexample_migration.migration_stamp import MigrationStamp, stamp_sort_key
    from wexample_migration.workdir.mixin.with_migration_workdir_mixin import (
        WithMigrationWorkdirMixin,
    )

    if not isinstance(app_workdir, WithMigrationWorkdirMixin):
        return FailureResponse(
            kernel=context.kernel,
            message=(
                "Current workdir does not support migrations. "
                "Mix WithMigrationWorkdirMixin into your workdir class and "
                "override get_migrations()."
            ),
        )

    if dry_run:
        context.io.log("Dry run — no changes will be written.")

    applied = app_workdir.migration_run(
        dry_run=dry_run,
        extras={"workdir": app_workdir, "kernel": context.kernel},
    )

    if applied:
        label = "Would apply" if dry_run else "Applied"
        result = SuccessResponse(
            kernel=context.kernel,
            message=f"{label}: {', '.join(applied)}",
        )
    else:
        result = "No pending migrations."

    if dry_run:
        return result

    # Final stamp = max(kernel.version, current applied state). The migration
    # cursor (seq) is kept only when it belongs to the resulting version —
    # otherwise it resets to 0 to leave room for future seq-1+ migrations
    # tagged for that version.
    kernel_version = context.kernel.workdir.get_setup_version()
    current = app_workdir.migration_read_stamp()

    kernel_key = stamp_sort_key(kernel_version, 0)
    current_key = (
        stamp_sort_key(current.version, current.seq) if current is not None else None
    )

    if current_key is None or kernel_key > current_key:
        new_stamp = MigrationStamp(version=kernel_version, seq=0)
    else:
        new_stamp = current

    app_workdir.migration_write_stamp(new_stamp)

    return result
