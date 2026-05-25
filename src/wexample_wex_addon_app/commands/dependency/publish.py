from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

if TYPE_CHECKING:
    from wexample_app.response.dict_response import DictResponse
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__dependency__publish(
    context: ExecutionContext,
    app_workdir: RepoWorkdir,
) -> DictResponse:
    from wexample_app.response.dict_response import DictResponse

    return DictResponse(
        kernel=context.kernel, content=app_workdir.publish_dependencies()
    )
