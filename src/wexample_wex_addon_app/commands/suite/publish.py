from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish packages to PyPI. Only publishes packages with changes since their last publication tag.",
)
def app__suite__publish(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    from wexample_prompt.enums.terminal_color import TerminalColor

    progress = context.get_or_create_progress(total=2, label="Publishing...")

    # Determine which packages need publication (changed since last tag)
    to_publish = app_workdir.compute_packages_to_publish()

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
