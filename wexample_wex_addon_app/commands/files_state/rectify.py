from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command()
def app__files_state__rectify(
        context: "ExecutionContext"
):
    # First try
    workdir = context.request.get_addon_manager().get_workdir()
    workdir.dry_run()