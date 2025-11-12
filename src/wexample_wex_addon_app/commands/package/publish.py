from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import (
    SuiteOrEachPackageMiddleware,
)
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="force", type=bool, default=False, is_flag=True)
@middleware(middleware=SuiteOrEachPackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to PyPI. Use --all-packages to publish all packages in suite.",
)
def app__package__publish(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
    force: bool = False,
) -> None:
    app_workdir.publish(force=force)
