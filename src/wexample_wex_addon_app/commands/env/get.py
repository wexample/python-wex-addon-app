from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Return the current app environment (APP_ENV from .wex/.env)")
def app__env__get(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
) -> str | None:
    return app_workdir.get_app_env()
