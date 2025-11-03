from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
    EachSuitePackageMiddleware,
)
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@option(name="loop", type=bool, default=False, is_flag=True)
@option(name="loop_limit", type=int, default=10)
@option(name="no_remote", type=bool, default=False, is_flag=True)
@option(name="filter_path", type=str, default=None)
@option(name="filter_operation", type=str, default=None)
@option(name="max", type=int, default=None)
@option(name="force", type=bool, default=False, is_flag=True)
@middleware(middleware=AppMiddleware)
@middleware(middleware=EachSuitePackageMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__file_state__rectify(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
    force: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    loop: bool = False,
    loop_limit: int = 10,
    no_remote: bool = False,
    filter_path: str | None = None,
    filter_operation: str | None = None,
    max: int = None,
) -> None:
    from wexample_filestate.enum.scopes import Scope

    if not dry_run:
        # Apply changes once, or keep looping until no operations remain (when --loop is set).
        iterations = 0
        while True:
            iterations += 1
            workdir = context.request.get_addon_manager().create_app_workdir()

            # Remove remote.
            scopes = (set(Scope) - {Scope.REMOTE}) if no_remote else None

            result = workdir.apply(
                interactive=(not yes),
                force=force,
                scopes=scopes,
                filter_path=filter_path,
                filter_operation=filter_operation,
                max=max,
            )

            if len(result.operations) == 0:
                pass_text = "pass" if iterations == 1 else "passes"
                context.io.success(
                    f"Rectification completed successfully after {iterations} {pass_text}."
                )
                break

            # Stop immediately after the first pass if looping is disabled.
            if not loop:
                operation_text = (
                    "operation" if len(result.operations) == 1 else "operations"
                )
                context.io.log(
                    f"Rectification pass completed; applied {len(result.operations)} {operation_text}."
                )
                break

            if iterations >= loop_limit:
                context.io.warning(
                    f"Loop limit reached ({iterations}/{loop_limit}); stopping further passes."
                )
                break

            context.io.log(
                f"Pass {iterations} completed with {len(result.operations)} operation(s); starting pass {iterations + 1} of {loop_limit}."
            )
    else:
        workdir = context.request.get_addon_manager().create_app_workdir(reload=True)
        workdir.dry_run()
