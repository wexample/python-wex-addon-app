from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version for one or all package of the suite.",
)
def app__test__run(
        context: ExecutionContext,
        app_workdir: AppMiddleware,
) -> None:
    app_workdir.shell_run_for_app(
        cmd=app_workdir.test_get_command()
    )
