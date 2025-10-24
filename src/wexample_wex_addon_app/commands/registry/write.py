from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

from wexample_wex_core.decorator.command import command


@command(type=COMMAND_TYPE_ADDON)
def app__registry__write(
    context: ExecutionContext,
) -> None:
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    workdir = context.request.get_addon_manager().app_workdir()

    registry = workdir.build_registry()

    context.io.success(
        message=f"Registry updated at: {cli_make_clickable_path(registry.get_path())}"
    )
