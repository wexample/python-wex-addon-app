from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option
from wexample_wex_core.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext
    from wexample_wex_core.package.framework_package import FrameworkPackage


@option(name="all", type=bool, default=False, is_flag=True)
@option(name="package", type=str)
@option(name="yes", type=bool, default=False, is_flag=True)
@command(
    description="Validate internal deps, propagate versions, and optionally commit/push."
)
def app__suite__prepare(
    context: ExecutionContext,
    all: bool | None = None,
    package: str | None = None,
    yes: bool = False,
) -> None:
    progress = context.get_or_create_progress(total=100)

    # Normalize input and initialize once
    package_name = package

    workdir = context.request.get_addon_manager().app_workdir(
        progress=progress.create_range_handle(to_step=10)
    )

    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager workdir: {workdir.get_path()}"
        )

    if workdir is None:
        return

    # Check options
    if all and package_name:
        context.io.error(
            "Options conflict: use either --all or --package <name>, not both."
        )
        return

    progress.advance(step=10)

    # Resolve target packages (for commit/push scope)
    target_packages: Iterable[FrameworkPackage]
    if all is True:
        target_packages = list(workdir.get_packages())
        if not target_packages:
            context.io.warning("No packages found in the suite to prepare.")
            return
    elif package_name:
        pkg = workdir.get_package(package_name=package_name)
        if not pkg:
            context.io.error(f"Package not found: {package_name}")
            return
        target_packages = [pkg]
    else:
        # Default: consider all (common expectation for prepare)
        target_packages = list(workdir.get_packages())

    # Validate and propagate
    progress.advance(step=10, label="Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies match.")

    workdir.packages_propagate_versions(progress=progress.create_range_handle(to=50))
    context.io.success("Versions updated.")

    # Commit/push if requested
    had_changes = _commit_or_warn_uncommitted(target_packages, yes, context)
    if had_changes and not yes:
        context.io.warning("Changes detected. Re-run with --yes to commit and push.")

    progress.finish(color=TerminalColor.GREEN, label="Preparation complete.")


def _commit_or_warn_uncommitted(
    packages: Iterable[FrameworkPackage], yes: bool, context: ExecutionContext
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
