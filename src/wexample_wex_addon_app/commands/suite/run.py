from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.validator.regex_validator import RegexValidator
from wexample_wex_core.const.globals import COMMAND_PATTERNS, COMMAND_TYPE_ADDON
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


@option(
    name="command",
    short_name="c",
    type=str,
    required=True,
    description="The full command to execute, e.g. app::info/show",
    validators=[RegexValidator(pattern=COMMAND_PATTERNS)],
)
@option(
    name="arguments",
    type=str,
    description='The arguments string, e.g. "-a arg -v --yes"',
)
@option(
    name="continue_on_error",
    short_name="coe",
    is_flag=True,
    type=bool,
    description="Continue execution on all packages even if one fails. Reports failures at the end.",
)
@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Execute a command on all packages of the suite.",
)
def app__suite__run(
    context: ExecutionContext,
    command: str,
    app_workdir: FrameworkPackageSuiteWorkdir,
    arguments: str = None,
    continue_on_error: bool = False,
) -> None:
    from wexample_helpers.helpers.shell import shell_split_cmd

    app_workdir.packages_execute_manager(
        command=command,
        arguments=shell_split_cmd(arguments) if arguments else None,
        fail_fast=not continue_on_error,
    )
