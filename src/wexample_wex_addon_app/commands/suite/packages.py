from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.response.dict_response import DictResponse
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Validate internal dependencies and propagate versions across all packages in the suite.",
)
def app__suite__packages(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    output = {}
    for package in app_workdir.get_ordered_packages():
        output[package.get_project_name()] = {
            "path": str(package.get_path()),
            "version": package.get_project_version(),
        }

    return DictResponse(kernel=context.kernel, content=output)
