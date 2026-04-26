from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="force", type=bool, default=False, is_flag=True)
@option(name="ignore_dependencies", type=bool, default=False, is_flag=True)
@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to package manager (npm, PyPI, packagist, etc.). Use --all-packages to publish all packages in suite.",
)
def app__suite__publish(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
    yes: bool = False,
    force: bool = False,
    ignore_dependencies: bool = False,
) -> None:
    from wexample_prompt.enums.terminal_color import TerminalColor

    from wexample_wex_addon_app.commands.suite.status import app__suite__status

    context.io.title("Suite publication status")
    app_workdir.manager_run_command(command=app__suite__status)

    # Fast path: check for changes before doing expensive validation/ordering.
    packages_with_changes: set[str] | None = None
    if not force:
        packages_with_changes = {
            p.get_package_name() for p in app_workdir.compute_packages_to_publish()
        }
        if not packages_with_changes:
            context.io.log("No packages have changes. Nothing to publish.")
            return

    if not ignore_dependencies:
        app_workdir.packages_validate_internal_dependencies_declarations()

    packages = app_workdir.get_ordered_packages()

    if not force:
        to_publish = [
            p.get_package_name()
            for p in packages
            if p.get_package_name() in packages_with_changes
        ]
        to_skip = [
            p.get_package_name()
            for p in packages
            if p.get_package_name() not in packages_with_changes
        ]
        if to_publish:
            context.io.log(f"Packages to publish ({len(to_publish)}):")
            context.io.list(to_publish)
        if to_skip:
            context.io.log(f"Packages with no changes, skipped ({len(to_skip)}):")
            context.io.list(to_skip)

    context.io.log("Starting deployment...")
    context.io.indentation_up()
    progress = context.io.progress(
        total=len(packages),
        print_response=False,
        color=TerminalColor.CYAN,
    ).get_handle()

    # Process packages in order leaf -> trunk.
    # Use manager for every command allow to use complete specific environment.
    for package in packages:
        progress.advance(label=f"Publishing {package.get_project_name()}", step=1)
        has_changes = (
            None if force else package.get_package_name() in packages_with_changes
        )
        package.release(
            force=force, interactive=not yes, has_changes=has_changes
        )

    # Commit propagated dependency-version updates for packages that were not
    # published (no real source changes).  Their config files (e.g. composer.json)
    # may have been dirtied by propagate_version of a published sibling; commit
    # those updates so they do not accumulate as false positives on future runs.
    if packages_with_changes is not None:
        for package in packages:
            if package.get_package_name() not in packages_with_changes:
                package.commit_propagated_dependency_updates()

    progress.finish(label="All packages published successfully")
