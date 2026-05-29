from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Deploy a published version of the app on the current host. "
        "Runs the app-level `.release/deploy` hook (if present) then restarts the app."
    ),
)
def app__release__deploy(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.commands.app.restart import app__app__restart

    def _hook(previous_value=None) -> None:
        app_workdir.manager_run(cmd=[".release/deploy", "--ignore-missing-command"])

    def _restart(previous_value=None) -> AbstractResponse:
        return context.kernel.run_function(app__app__restart, arguments={})

    return QueuedCollectionResponse(
        kernel=context.kernel,
        content=[_hook, _restart],
    )
