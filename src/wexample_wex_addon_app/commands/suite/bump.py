from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(description="Bump version for every package of the suite.")
def app__suite__bump(
        context: ExecutionContext,
) -> None:
    # Now we can initialize.
    workdir = context.request.get_addon_manager().app_workdir()

    for package in workdir.get_packages():
        package.bump()
