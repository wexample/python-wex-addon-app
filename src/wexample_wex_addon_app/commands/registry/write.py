from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__registry__write(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
) -> None:
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    registry = app_workdir.get_registry_file(rebuild=True)

    context.io.success(
        message=f"Registry updated at: {cli_make_clickable_path(registry.get_path())}"
    )
