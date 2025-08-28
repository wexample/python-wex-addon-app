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
    context.get_or_create_progress(total=6, label="Preparing publication...")

    # Avoid to initialize workdir before this.
    from wexample_wex_addon_app.commands.files_state.rectify import (
        app__files_state__rectify,
    )

    context.create_progress_range(to=1)

    app__files_state__rectify.function(
        context=context,
        yes=yes,
    )

    progress = context.finish_progress(current=1)

    # Now we can initialize.
    workdir = context.request.get_addon_manager().app_workdir(
        progress=progress.create_range_handle(to=2)
    )

    # Ensure we are in the correct workdir type before using it.
    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager workdir: {workdir.get_path()}"
        )
        return

    has_changes = False
    for package in workdir.get_packages():
        if package.has():
            has_changes = True

            if yes:
                package.commit_and_push(
                    progress=progress.create_range_handle(to=3)
                )
            else:
                context.io.warning(f"Package {package.get_package_name()} has uncommitted changes.")

    if has_changes and not yes:
        context.io.warning("Stopping due to uncommitted changes.")
        return

    progress.advance(step=1, label="Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies match.")

    progress.advance(step=1, label="Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")

    workdir.publish_packages(
        progress=progress.create_range_handle(to=6),
    )

    progress.finish(color=TerminalColor.GREEN)
    context.io.success("All packages published.")
