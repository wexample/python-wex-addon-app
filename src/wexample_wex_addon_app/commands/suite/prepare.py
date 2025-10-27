from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Validate internal dependencies and propagate versions across all packages in the suite. Use app::suite/commit-and-push afterwards to commit changes.",
)
def app__suite__prepare(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    from wexample_prompt.enums.terminal_color import TerminalColor

    progress = context.get_or_create_progress(total=100)

    # Validate internal dependencies
    progress.advance(step=10, label="Checking internal dependencies...")
    app_workdir.packages_validate_internal_dependencies_declarations()
    context.io.success("Internal dependencies match.")

    # Propagate versions
    progress.advance(step=10, label="Propagating versions...")
    app_workdir.packages_propagate_versions(
        progress=progress.create_range_handle(to=80)
    )
    context.io.success("Versions propagated successfully.")

    progress.finish(color=TerminalColor.GREEN, label="Preparation complete.")

    context.io.info("To commit and push changes, run: app::suite/commit-and-push --yes")
