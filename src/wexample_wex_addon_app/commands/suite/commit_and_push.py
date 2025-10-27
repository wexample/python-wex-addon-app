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
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Commit and push changes for all packages in the suite that have uncommitted changes.",
)
def app__suite__commit_and_push(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
    yes: bool = False,
) -> None:
    packages = list(app_workdir.get_packages())
    has_changes = False

    for package in packages:
        package_name = package.get_package_name()

        if package.has_working_changes():
            has_changes = True

            if yes:
                context.io.info(f"Committing and pushing changes for {package_name}...")
                package.commit_changes()
                package.push_changes()
                context.io.success(f"Successfully committed and pushed {package_name}.")
            else:
                context.io.warning(f"Package {package_name} has uncommitted changes.")
        else:
            context.io.log(f"Package {package_name} has no uncommitted changes.")

    if has_changes and not yes:
        context.io.warning(
            "Changes detected. Re-run with --yes to commit and push all packages."
        )
    elif not has_changes:
        context.io.info("No uncommitted changes found in any package.")
