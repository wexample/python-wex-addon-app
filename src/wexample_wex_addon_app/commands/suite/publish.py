from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.package_suite_middleware import PackageSuiteMiddleware
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to PyPI. Use --all-packages to publish all packages in suite.",
)
def app__suite__publish(
        context: ExecutionContext,
        app_workdir: CodeBaseWorkdir,
) -> None:
    pass