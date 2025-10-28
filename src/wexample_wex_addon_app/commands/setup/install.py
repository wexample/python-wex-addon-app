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


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Install package manager into suite or packages",
)
@option(name="env", type=str, default=None)
def app__setup__install(
        context: ExecutionContext,
        app_workdir: FrameworkPackageSuiteWorkdir,
        env: str | None = None
) -> None:
    app_workdir.setup_install(env)
