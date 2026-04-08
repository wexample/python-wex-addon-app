from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.list_response import ListResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="List app domains")
def app__domain__list(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
) -> ListResponse:
    from wexample_app.response.list_response import ListResponse

    return ListResponse(
        kernel=context.kernel,
        content=app_workdir.get_domains_config()["domains"],
    )
