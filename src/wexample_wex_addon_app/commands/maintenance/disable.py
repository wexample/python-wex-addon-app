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
    description=(
        "Deactivate maintenance mode on the app. Triggers the `maintenance/disable` "
        "service hook on every installed service that declares it (e.g. laravel → "
        "`php artisan up`). Apps add custom behavior via @attach."
    ),
)
def app__maintenance__disable(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    app_manager = AppAddonManager.from_kernel(context.kernel)
    results = app_manager.run_service_hook(
        hook="maintenance/disable",
        app_workdir=app_workdir,
    )
    context.io.log(f"Maintenance disabled ({len(results)} service(s) hooked)")
