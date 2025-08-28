from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option
from wexample_wex_core.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_prompt.enums.terminal_color import TerminalColor

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


# ----- Internal helpers -----------------------------------------------------

def _init_app_workdir(context: "ExecutionContext", progress) -> FrameworkPackageSuiteWorkdir | None:
    """Create an app workdir and ensure its type is valid for a suite.

    Returns the workdir or None if the current path is not a suite manager workdir.
    """
    workdir = context.request.get_addon_manager().app_workdir(
        progress=progress.create_range_handle(to_step=2)
    )
    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager workdir: {workdir.get_path()}"
        )
        return None
    return workdir


def _validate_and_propagate(workdir: FrameworkPackageSuiteWorkdir, context: "ExecutionContext", progress) -> None:
    """Validate internal dependencies and propagate versions with progress updates."""
    progress.advance(step=1, label="Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies match.")

    progress.advance(step=1, label="Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")


def _commit_or_warn_uncommitted(packages, yes: bool, context: "ExecutionContext", progress) -> bool:
    """Commit/push uncommitted changes if confirmed, else warn and remember there were changes.

    Returns True if there were uncommitted changes detected in at least one package.
    """
    has_changes = False
    # Make per-package progress explicit
    # Allocate exactly one outer progress unit for this phase, and spread it over packages
    progress_range = progress.create_range_handle(to_step=1, total=len(packages))
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
        progress_range.advance(step=1)
    return has_changes


def _stabilize_to_publish(
    context: "ExecutionContext",
    base_progress,
    workdir: FrameworkPackageSuiteWorkdir,
    initial_to_publish,
    max_loops: int = 3,
):
    """Recompute the set of packages to publish until stable or max_loops.

    Returns the stable list of packages to publish.
    """
    to_publish = list(initial_to_publish)
    loop = 0
    while to_publish and loop < max_loops:
        loop += 1

        # Recreate workdir after potential rectify/pins updates
        workdir = context.request.get_addon_manager().app_workdir(
            progress=base_progress.create_range_handle(to_step=2)
        )

        # Re-validate and re-propagate
        base_progress.advance(step=1, label="Re-checking internal dependencies...")
        workdir.packages_validate_internal_dependencies_declarations()
        base_progress.advance(step=1, label="Re-propagating versions...")
        workdir.packages_propagate_versions()

        new_to_publish = workdir.compute_packages_to_publish()

        old_set = {p.get_package_name() for p in to_publish}
        new_set = {p.get_package_name() for p in new_to_publish}
        if new_set == old_set:
            break
        to_publish = new_to_publish

    return to_publish


@option(name="yes", type=bool, default=False, is_flag=True)
@command(description="Publish the Python package to PyPI.")
def app__suite__publish(
        context: ExecutionContext,
        yes: bool = False,
) -> None:
    progress = context.get_or_create_progress(total=6, label="Preparing publication...")

    # Initialization and checks
    workdir = _init_app_workdir(context, progress)
    if workdir is None:
        return

    # Validate internal deps and propagate versions
    _validate_and_propagate(workdir, context, progress)

    # Commit/push uncommitted changes if confirmed, else stop.
    packages = workdir.get_packages()
    has_changes = _commit_or_warn_uncommitted(packages, yes, context, progress)
    if has_changes and not yes:
        context.io.warning("Stopping due to uncommitted changes.")
        return

    # Determine which packages need publication (changed since last tag)
    to_publish = workdir.compute_packages_to_publish()

    # Stabilization loop: if publishing some packages affects others (pin updates),
    # run rectify + rebuild workdir + re-propagate versions, then recompute.
    to_publish = _stabilize_to_publish(
        context=context,
        base_progress=progress,
        workdir=workdir,
        initial_to_publish=to_publish,
        max_loops=3,
    )

    if not to_publish:
        context.io.info(
            "No packages to publish (no changes since last publication tags)."
        )
        return

    # Allocate remaining outer progress units for publishing phase
    progress_range = progress.create_range_handle(to_step=3, total=len(to_publish))
    for package in to_publish:
        package.publish(
            progress=progress_range.create_range_handle(to_step=1),
        )
        # Add tag after successful publication
        package.add_publication_tag()
        progress_range.advance(step=1)

    progress_range.finish()

    progress.finish(color=TerminalColor.GREEN, label="All packages published.")
