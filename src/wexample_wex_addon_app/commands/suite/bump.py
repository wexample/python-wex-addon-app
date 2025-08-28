from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="all", type=bool, default=False, is_flag=True)
@option(name="package", type=str)
@command(description="Bump version for one or all package of the suite.")
def app__suite__bump(
        context: ExecutionContext,
        all: bool | None = None,
        package: str | None = None
) -> None:
    # Normalize input and initialize once.
    package_name = package
    workdir = context.request.get_addon_manager().app_workdir()

    # Guard against conflicting options.
    if all and package_name:
        context.io.error("Options conflict: use either --all or --package <name>, not both.")
        return

    if all is True:
        packages = list(workdir.get_packages())
        if not packages:
            context.io.warning("No packages found in the suite to bump.")
            return

        context.io.info(f"Bumping versions for {len(packages)} package(s)...")
        bumped = 0
        for package in packages:
            package.bump()
            bumped += 1
            context.io.info(f"- Bumped: {getattr(package, 'name', str(package))}")

        workdir.packages_propagate_versions()
        context.io.info(f"Version propagation completed. Successfully bumped {bumped}/{len(packages)} package(s).")

    elif package_name:
        package = workdir.get_package(package_name=package_name)

        if not package:
            context.io.error(f"Package not found: {package_name}")
            return

        context.io.info(f"Bumping version for package: {package_name}...")
        package.bump()

        workdir.packages_propagate_versions()
        context.io.info(f"Version propagation completed for {package_name}.")

    else:
        context.io.error("Missing option. Use --all to bump every package or --package <name> to bump a specific one.")
