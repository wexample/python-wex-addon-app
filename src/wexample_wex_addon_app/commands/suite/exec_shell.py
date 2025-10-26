from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.helpers.shell import shell_split_cmd
from wexample_wex_addon_app.middleware.package_suite_middleware import PackageSuiteMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import FrameworkPackageSuiteWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="command",
    type=str,
    required=True,
    description="The full shell command to execute, e.g. \"ls -la\"",
)
@middleware(
    middleware=PackageSuiteMiddleware
)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version for one or all package of the suite.",
)
def app__suite__exec_shell(
        context: ExecutionContext,
        command: str,
        app_path: str | None = None
) -> None:
    workdir = context.request.get_addon_manager().app_workdir(path=app_path, reload=True)

    if workdir:
        if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
            context.io.info(
                message=f"The app workdir `{workdir.get_path()}` is of type {workdir.__class__.__name__} and not a subclass of packages suite manager."
            )
        else:
            workdir.packages_execute_shell(
                cmd=shell_split_cmd(command)
            )
