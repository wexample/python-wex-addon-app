from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__info__show(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
) -> None:
    from wexample_app.const.env import ENV_NAME_LOCAL
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    context.io.properties(
        {
            "Name": app_workdir.get_item_name(),
            "Version": app_workdir.get_project_version(),
            "Path": cli_make_clickable_path(path=app_workdir.get_path()),
        },
        title="Application info",
    )

    # Show local libraries if configured
    local_libraries = app_workdir.get_local_libraries_paths(env=ENV_NAME_LOCAL)
    if local_libraries:
        context.io.title("Environment: local")
        context.io.log("Libraries:", indentation=1)
        for lib_path in local_libraries:
            context.io.log(f"• {cli_make_clickable_path(lib_path)}", indentation=2)
