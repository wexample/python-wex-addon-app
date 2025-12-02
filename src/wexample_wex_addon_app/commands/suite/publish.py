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

    if not ignore_dependencies:
        app_workdir.packages_validate_internal_dependencies_declarations()

    packages = app_workdir.get_ordered_packages()

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
        package.publish_bumped(force=force, interactive=not yes)

    progress.finish(label="All packages published successfully")
