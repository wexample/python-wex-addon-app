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

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Propagate package versions across all dependents in the suite.",
)
def app__suite__propagate_versions(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    context.io.info("Starting version propagation across all packages...")

    app_workdir.packages_propagate_versions()

    context.io.success("Version propagation completed successfully.")
