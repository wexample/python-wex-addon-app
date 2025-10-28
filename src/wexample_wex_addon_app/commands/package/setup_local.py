from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Install package manager into suite or packages",
)
def app__package__setup_local(
        context: ExecutionContext,
        app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    from wexample_app.const.globals import APP_PATH_APP_MANAGER
    suite_workdir = app_workdir.get_suite_workdir()
    app_path = app_workdir.get_path()

    for package in suite_workdir.get_ordered_packages():
        package_path = package.get_path()
        # Ignore itself
        if package_path != app_path:
            context.io.log(str(app_path / APP_PATH_APP_MANAGER))
            app_workdir.shell_run_from_path(
                path=app_path / APP_PATH_APP_MANAGER,
                cmd=[
                    "pip",
                    "install",
                    "-e",
                    str(package_path),
                    "--no-deps",
                ])
