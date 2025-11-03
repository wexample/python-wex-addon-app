from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.response.app_info_response import AppInfoResponse
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext
    from wexample_app.response.dict_response import DictResponse


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__info__show(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
) -> DictResponse:
    return AppInfoResponse(app_workdir=app_workdir, kernel=context.kernel)
