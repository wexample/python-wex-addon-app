from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
    EachSuitePackageMiddleware,
)
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import FrameworkPackageSuiteWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="ignore_suite", type=bool, default=False, is_flag=True)
@middleware(middleware=AppMiddleware)
@middleware(middleware=EachSuitePackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version for a package. Use --all-packages to bump all packages in a suite.",
)
def app__package__bump(
        context: ExecutionContext,
        app_workdir: CodeBaseWorkdir,
        yes: bool = False,
        ignore_suite: bool = False
) -> None:
    if isinstance(app_workdir, FrameworkPackageSuiteWorkdir) and ignore_suite:
        return

    package_name = app_workdir.get_package_name()
    context.io.info(f"Bumping version for package: {package_name}...")

    if app_workdir.bump(interactive=not yes):
        context.io.success(f"Successfully bumped {package_name}.")
    else:
        context.io.log(f"Bump aborted.")
