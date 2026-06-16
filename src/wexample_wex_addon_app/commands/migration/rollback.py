from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Rollback the last applied migration on the current app",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DB,
        DomainTag.MIGRATION,
        EffectTag.DESTRUCTIVE,
        EffectTag.WRITE,
        AudienceTag.DANGEROUS,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__migration__rollback(context: ExecutionContext, app_workdir: ManagedWorkdir):
    from wexample_app.response.failure_response import FailureResponse
    from wexample_app.response.success_response import SuccessResponse
    from wexample_migration.workdir.mixin.with_migration_workdir_mixin import (
        WithMigrationWorkdirMixin,
    )

    kernel = context.kernel

    if not isinstance(app_workdir, WithMigrationWorkdirMixin):
        return FailureResponse(
            kernel=kernel,
            message=(
                "Current workdir does not support migrations. "
                "Mix WithMigrationWorkdirMixin into your workdir class and "
                "override get_migrations()."
            ),
        )

    rolled_back = app_workdir.migration_rollback(
        extras={"workdir": app_workdir, "kernel": kernel}
    )

    if rolled_back:
        return SuccessResponse(
            kernel=kernel, message=f"Rolled back: {rolled_back}"
        )
    return "Nothing to rollback."
