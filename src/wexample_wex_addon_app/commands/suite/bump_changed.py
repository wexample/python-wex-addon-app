from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wexample_wex_core.context.execution_context import ExecutionContext
    from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@option(name="all", type=bool, default=False, is_flag=True)
@option(name="package", type=str)
@option(name="yes", type=bool, default=False, is_flag=True)
@command(type=COMMAND_TYPE_ADDON,
    description="Bump versions only for packages that have new content (HEAD not tagged), propagate versions, and optionally commit/push."
)
def app__suite__bump_changed(
    context: ExecutionContext,
    all: bool | None = None,
    package: str | None = None,
    yes: bool = False,
) -> None:
    # Init workdir
    workdir = _init_app_workdir(context)
    if workdir is None:
        return

    # Validate options
    if all and package:
        context.io.error(
            "Options conflict: use either --all or --package <name>, not both."
        )
        return

    # Determine candidate set: either the whole suite or a single package
    candidates: Iterable[CodeBaseWorkdir]
    if all is True:
        candidates = list(workdir.get_packages())
        if not candidates:
            context.io.warning("No packages found in the suite.")
            return
    elif package:
        pkg = workdir.get_package(package_name=package)
        if not pkg:
            context.io.error(f"Package not found: {package}")
            return
        candidates = [pkg]
    else:
        # Default to all when no selector is provided
        candidates = list(workdir.get_packages())

    # Compute which packages actually have new content (need publish) and filter by candidates
    to_publish = workdir.compute_packages_to_publish()
    to_publish_names = {p.get_package_name() for p in to_publish}
    targets = [p for p in candidates if p.get_package_name() in to_publish_names]

    if not targets:
        context.io.info("No packages with new content to bump.")
        return

    # Bump only targets with new content
    for pkg in targets:
        context.io.info(f"Bumping: {pkg.get_package_name()}...")
        pkg.bump(interactive=not yes)

    # After bumping, propagate versions across the suite
    context.io.info("Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")

    # Commit/push changes where needed
    changed = _commit_or_warn_uncommitted(workdir.get_packages(), yes, context)
    if changed and not yes:
        context.io.warning("Changes detected. Re-run with --yes to commit and push.")


def _commit_or_warn_uncommitted(
    packages: Iterable[CodeBaseWorkdir], yes: bool, context: ExecutionContext
) -> bool:
    has_changes = False
    for package in packages:
        if package.has_working_changes():
            has_changes = True
            if yes:
                package.commit_changes()
                package.push_changes()
            else:
                context.io.warning(
                    f"Package {package.get_package_name()} has uncommitted changes."
                )
        else:
            context.io.log(
                f"Package {package.get_package_name()} has no uncommitted changes."
            )
    return has_changes


def _init_app_workdir(context: ExecutionContext) -> FrameworkPackageSuiteWorkdir | None:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )

    workdir = context.request.get_addon_manager().app_workdir()
    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path of {type(workdir)} is not a suite manager workdir: {workdir.get_path()}"
        )
        return None
    return workdir
