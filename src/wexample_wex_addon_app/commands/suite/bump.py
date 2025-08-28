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
    # Passed variable should be named "package".
    package_name = package

    if all is True:
        # Now we can initialize.
        workdir = context.request.get_addon_manager().app_workdir()
        # for package in workdir.get_packages():
        #     package.bump()
        workdir.packages_propagate_versions()
    elif package is not None:
        # Now we can initialize.
        workdir = context.request.get_addon_manager().app_workdir()

        package = workdir.get_package(
            package_name=package_name
        )
        if package:
            # package.bump()
            workdir.packages_propagate_versions()
        else:
            context.io.warning(f'Package not found: {package_name}')
    else:
        context.io.warning('You should choose --all or --package [name] option')
