from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@option(name="loop", type=bool, default=False, is_flag=True)
@option(name="limit", type=int, default=10)
@option(name="no_remote", type=bool, default=False, is_flag=True)
@command()
def app__files_state__rectify(
    context: ExecutionContext,
    yes: bool = False,
    dry_run: bool = False,
    loop: bool = False,
    limit: int = 10,
    no_remote: bool = False,
) -> None:
    from wexample_filestate.enum.scopes import Scope

    if not dry_run:
        # Apply changes once, or keep looping until no operations remain (when --loop is set).
        iterations = 0
        while True:
            workdir = context.request.get_addon_manager().app_workdir(reload=True)

            # Remove remote.
            scopes = (set(Scope) - {Scope.REMOTE}) if no_remote else None
            result = workdir.apply(interactive=(not yes), scopes=scopes)

            if len(result.operations) == 0:
                context.io.success(
                    f"No remaining operations; rectification converged after {iterations} pass(es)."
                )
                break

            # Stop immediately after the first pass if looping is disabled.
            if not loop:
                context.io.log(
                    f"Rectification pass completed; detected {len(result.operations)} operation(s)."
                )
                break

            iterations += 1
            if iterations >= limit:
                context.io.warning(
                    f"Loop limit reached ({iterations}/{limit}); stopping further passes."
                )
                break

            context.io.log(
                f"Remaining operations detected; starting pass {iterations} of {limit}."
            )
    else:
        workdir = context.request.get_addon_manager().app_workdir(reload=True)
        workdir.dry_run()
