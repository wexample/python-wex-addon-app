from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Show the migration status of the current app",
)
def app__migration__status(
    context: ExecutionContext, app_workdir: ManagedWorkdir
):
    from wexample_app.response.failure_response import FailureResponse
    from wexample_app.response.properties_response import PropertiesResponse
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

    status = app_workdir.migration_status(
        extras={"workdir": app_workdir, "kernel": context.kernel}
    )

    return PropertiesResponse(
        kernel=context.kernel,
        title="Migration status",
        properties={
            "Current version": status["current_version"] or "none",
            "Applied": ", ".join(status["applied"]) if status["applied"] else "(none)",
            "Pending": (
                ", ".join(status["pending"])
                if status["pending"]
                else "(up to date)"
            ),
        },
    )
