from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option
from wexample_wex_core.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@command(description="Publish the Python package to PyPI.")
def app__suite__publish(
        context: ExecutionContext,
        yes: bool = False,
) -> None:
    from wexample_prompt.enums.terminal_color import TerminalColor

    progress = context.get_or_create_progress(total=6, label="Preparing publication...")

    # Now we can initialize.
    workdir = context.request.get_addon_manager().app_workdir(
        progress=progress.create_range_handle(to=2)
    )

    progress.advance(step=1, label="Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies match.")

    # Ensure we are in the correct workdir type before using it.
    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager workdir: {workdir.get_path()}"
        )
        return

    has_changes = False
    progress_range = progress.create_range_handle(to=3)

    progress.advance(step=1, label="Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")

    # Commit/push uncommitted changes if confirmed, else stop.
    packages = workdir.get_packages()
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

    if has_changes and not yes:
        context.io.warning("Stopping due to uncommitted changes.")
        return

    # Determine which packages need publication (changed since last tag)
    to_publish = workdir.compute_packages_to_publish()

    # Stabilization loop: if publishing some packages affects others (pin updates),
    # run rectify + rebuild workdir + re-propagate versions, then recompute.
    max_loops = 3
    loop = 0
    while to_publish and loop < max_loops:
        loop += 1

        # Recreate workdir after rectify
        workdir = context.request.get_addon_manager().app_workdir(
            progress=progress.create_range_handle(to=4)
        )

        # Validate and propagate again
        progress.advance(step=1, label="Re-checking internal dependencies...")
        workdir.packages_validate_internal_dependencies_declarations()
        progress.advance(step=1, label="Re-propagating versions...")
        workdir.packages_propagate_versions()

        new_to_publish = workdir.compute_packages_to_publish()

        # If stable, break; else continue with the new set
        old_set = {p.get_package_name() for p in to_publish}
        new_set = {p.get_package_name() for p in new_to_publish}
        if new_set == old_set:
            break
        to_publish = new_to_publish

    if not to_publish:
        context.io.info(
            "No packages to publish (no changes since last publication tags)."
        )
        return

    progress_range = progress.create_range_handle(to=6, total=len(to_publish))
    for package in to_publish:
        package.publish(
            progress=progress_range.create_range_handle(
                to=progress.response.current + 1,
            ),
        )
        # Add tag after successful publication
        package.add_publication_tag()
        progress_range.advance(step=1)

    progress_range.finish()

    progress.finish(color=TerminalColor.GREEN, label="All packages published.")
