from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Restart the app (stop then start)")
def app__app__restart(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.commands.app.stop import app__app__stop

    def _stop(previous_value=None) -> AbstractResponse:
        return context.kernel.run_function(app__app__stop, arguments={"force": True})

    def _start(previous_value=None) -> AbstractResponse:
        from wexample_wex_addon_app.commands.app.start import app__app__start

        return context.kernel.run_function(app__app__start)

    return QueuedCollectionResponse(kernel=context.kernel, content=[_stop, _start])
