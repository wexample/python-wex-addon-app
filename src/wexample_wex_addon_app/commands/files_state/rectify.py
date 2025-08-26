from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@option(name="loop", type=bool, default=True, is_flag=True)
@command()
def app__files_state__rectify(
        context: ExecutionContext,
        yes: bool,
        dry_run: bool,
        loop: bool,
) -> None:
    workdir = context.request.get_addon_manager().app_workdir()

    if not dry_run:
        # Apply changes, and if --loop is enabled, keep applying until there are no operations left.
        while True:
            result = workdir.apply(interactive=(not yes))

            # Stop immediately if loop is disabled.
            if not loop:
                break

            if len(result.operations) == 0:
                break
    else:
        workdir.dry_run()
