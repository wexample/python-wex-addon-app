from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__registry__build(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
):
    from wexample_app.response.success_response import SuccessResponse
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    registry = app_workdir.get_registry_file(rebuild=True)

    return SuccessResponse(
        kernel=context.kernel,
        message=f"Registry updated at: {cli_make_clickable_path(registry.get_path())}",
    )
