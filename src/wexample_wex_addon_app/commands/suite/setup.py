from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import SuiteOrEachPackageMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=SuiteOrEachPackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Install package manager into suite or packages",
)
def app__suite__setup(
        context: ExecutionContext,
        app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

    app_workdir.packages_execute_shell(cmd=[
        str(APP_PATH_BIN_APP_MANAGER),
        "setup"
    ])
