from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Run one-time idempotent setup for all active services",
)
def app__app__setup(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    AppAddonManager.from_kernel(context.kernel).run_service_hook(
        hook="service/setup",
        app_workdir=app_workdir,
    )
