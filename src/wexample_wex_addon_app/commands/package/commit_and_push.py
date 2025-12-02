from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import (
    SuiteOrEachPackageMiddleware,
)
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=SuiteOrEachPackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Commit and push changes for a package. Use --all-packages to apply to all packages in suite.",
)
def app__package__commit_and_push(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
) -> None:
    from wexample_helpers_git.const.common import GIT_BRANCH_MAIN

    package_name = app_workdir.get_package_name()
    app_workdir.commit_changes()
    app_workdir.push_to_deployment_remote(branch_name=GIT_BRANCH_MAIN)
    context.io.success(f"Pushed {package_name}.")
