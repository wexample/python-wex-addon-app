from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@option(
    name="format",
    type=str,
    default="html",
    description="The output format of the report",
)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version for one or all package of the suite.",
)
def app__test__run(
    context: ExecutionContext, app_workdir: AppMiddleware, format: str | None = None
) -> None:
    app_workdir.test_run(format=format)
