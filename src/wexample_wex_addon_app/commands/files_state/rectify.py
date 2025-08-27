from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@option(name="loop", type=bool, default=True, is_flag=True)
@option(name="limit", type=int, default=10)
@command()
def app__files_state__rectify(
        context: ExecutionContext,
        yes: bool = False,
        dry_run: bool = False,
        loop: bool = True,
        limit: int = 10,
) -> None:
    if not dry_run:
        # Apply changes, and if --loop is enabled, keep applying until there are no operations left.
        iterations = 0
        while True:
            workdir = context.request.get_addon_manager().app_workdir(
                reload=True
            )
            
            result = workdir.apply(interactive=(not yes))

            # Stop immediately if loop is disabled.
            if not loop:
                break

            if len(result.operations) == 0:
                context.io.success(
                    f"Rectifications completed after {iterations} iteration(s)."
                )
                break

            iterations += 1
            if iterations >= limit:
                context.io.success(
                    f"Rectifications stopped after {iterations} iteration(s) (limit reached)."
                )
                break
            context.io.log(
                "Previous rectification found remaining changes; continuing..."
            )
    else:
        workdir.dry_run()
