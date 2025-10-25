from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@command(type=COMMAND_TYPE_ADDON, description="Publish the Python package to PyPI.")
def app__suite__publish(
    context: ExecutionContext,
) -> None:
    from wexample_prompt.enums.terminal_color import TerminalColor

    progress = context.get_or_create_progress(total=2, label="Publishing...")

    # Initialization
    workdir = _init_app_workdir(context, progress)
    if workdir is None:
        return

    # Determine which packages need publication (changed since last tag)
    to_publish = workdir.compute_packages_to_publish()

    if not to_publish:
        context.io.info(
            "No packages to publish (no changes since last publication tags)."
        )
        progress.finish(color=TerminalColor.GREEN, label="Nothing to publish.")
        return

    # Publish only, no bump/propagation/commit here; skip if already tagged for current version
    progress_range = progress.create_range_handle(to_step=2, total=len(to_publish))
    for package in to_publish:
        current_tag = package.get_publication_tag_name()
        last_tag = package.get_last_publication_tag()

        if last_tag == current_tag:
            context.io.info(
                f"{package.get_package_name()} already published as {current_tag}; skipping."
            )
            progress_range.advance(step=1)
            continue

        package.publish(
            progress=progress_range.create_range_handle(to_step=1),
        )
        # Tag after successful publication
        package.add_publication_tag()
        progress_range.advance(step=1)

    progress_range.finish()
    progress.finish(color=TerminalColor.GREEN, label="All packages published.")


def _init_app_workdir(
    context: ExecutionContext, progress
) -> FrameworkPackageSuiteWorkdir | None:
    """Create an app workdir and ensure its type is valid for a suite.

    Returns the workdir or None if the current path is not a suite manager workdir.
    """
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )

    workdir = context.request.get_addon_manager().app_workdir()
    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager workdir: {workdir.get_path()}"
        )
        return None
    return workdir
