from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@command()
def app__files_state__rectify(
    context: ExecutionContext,
    yes: bool,
    dry_run: bool,
) -> None:
    workdir = context.request.get_addon_manager().app_workdir()

    if not dry_run:
        workdir.apply(interactive=(not yes))
    else:
        workdir.dry_run()
