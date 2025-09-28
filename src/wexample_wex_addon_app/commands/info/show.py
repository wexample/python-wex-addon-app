from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

from wexample_wex_core.decorator.command import command


@command()
def app__info__show(
        context: ExecutionContext,
) -> None:
    from wexample_helpers.helpers.cli import cli_make_clickable_path
    workdir = context.request.get_addon_manager().app_workdir()

    context.io.properties({
        "name": workdir.get_item_name(),
        "version": workdir.get_project_version(),
        "path": cli_make_clickable_path(
            path=workdir.get_path()
        ),
    }, title="Application info")
