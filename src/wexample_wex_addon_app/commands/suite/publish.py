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
    context.get_or_create_progress(total=5, label="Preparing publication...")

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

    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager: {workdir.get_path()}"
        )
        return

    progress.advance(step=2, label="Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies matches.")

    progress.advance(step=3, label="Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")

    workdir.publish_packages(
        progress=progress.create_range_handle(to=5),
        commit_and_push=yes
    )

    progress.finish()
    context.io.success("All packages published")
