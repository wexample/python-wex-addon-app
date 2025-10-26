from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.helpers.shell import shell_split_cmd
from wexample_helpers.validator.regex_validator import RegexValidator
from wexample_wex_addon_app.middleware.each_suite_package_middleware import EachSuitePackageMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import FrameworkPackageSuiteWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON, COMMAND_PATTERNS
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=EachSuitePackageMiddleware)
@option(
    name="command",
    type=str,
    required=True,
    description="The full command to execute, e.g. app::info/show",
    validators=[RegexValidator(pattern=COMMAND_PATTERNS)]
)
@option(
    name="arguments",
    type=str,
    description="The arguments string, e.g. \"-a arg -v --yes\"",
)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version for one or all package of the suite.",
)
def app__suite__exec_command(
        context: ExecutionContext,
        command: str,
        arguments: str = None,
        app_path: str | None = None
) -> None:
    workdir = context.request.get_addon_manager().app_workdir(path=app_path, reload=True)

    if workdir:
        if not isinstance(workdir, FrameworkPackageSuiteWorkdir):
            context.io.info(
                message=f"The app workdir `{workdir.get_path()}` is of typs {workdir.__class__.__name__} and not a subclass of packages suite manager."
            )
        else:
            cmd = [command]
            if arguments is not None:
                cmd.extend(shell_split_cmd(arguments))

            cmd.extend([
                "--indentation-level",
                str(context.io.indentation + 1)
            ])

            workdir.packages_execute_shell(
                cmd=cmd
            )
