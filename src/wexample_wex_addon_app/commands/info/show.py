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
def app__info__show(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
) -> None:
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    context.io.properties(
        {
            "Name": app_workdir.get_item_name(),
            "Version": app_workdir.get_project_version(),
            "Path": cli_make_clickable_path(path=app_workdir.get_path()),
        },
        title="Application info",
    )
