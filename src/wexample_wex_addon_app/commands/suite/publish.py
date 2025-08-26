from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command
from wexample_wex_core.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(description="Publish the Python package to PyPI.")
def app__suite__publish(
    context: ExecutionContext,
) -> None:
    workdir = context.request.get_addon_manager().app_workdir()

    if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
        context.io.warning(
            f"The current path is not a suite manager: {workdir.get_path()}"
        )
        return

    context.io.task("Checking internal dependencies...")
    workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies matches.")

    context.io.task("Propagating versions across packages...")
    workdir.packages_propagate_versions()
    context.io.success("Versions updated.")
