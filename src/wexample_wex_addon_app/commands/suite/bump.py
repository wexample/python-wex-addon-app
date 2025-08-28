from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="all", type=bool, default=False, is_flag=True)
@option(name="package", type=str)
@command(description="Bump version for every package of the suite.")
def app__suite__bump(
        context: ExecutionContext,
        all: bool | None = None,
        package: str | None = None
) -> None:
    # Now we can initialize.
    workdir = context.request.get_addon_manager().app_workdir()

    if all is True:
        for package in workdir.get_packages():
            package.bump()
    elif package is not None:
        package = workdir.get_package(
            package_name=package
        )
        package.bump()
    else:
        context.io.warning('You should choose --all or --package [name] option')
