from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_app.response.dict_response import DictResponse
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__info__show(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> DictResponse:
    from wexample_wex_addon_app.response.app_info_response import AppInfoResponse

    return AppInfoResponse(app_workdir=app_workdir, kernel=context.kernel)
