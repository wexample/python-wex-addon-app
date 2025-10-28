from __future__ import annotations

from typing import TYPE_CHECKING

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
    description="Install package manager into suite or packages",
)
def app__suite__setup_local(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    from wexample_wex_addon_app.commands.package.setup_local import (
        app__package__setup_local,
    )

    # # TODO Ensure if we don't need to pass through kernel.
    # app__setup__install.function(context, app_workdir)
    #
    # app_workdir.packages_execute_manager(
    #     command=context.request.resolver.build_command_from_function(
    #         command_wrapper=app__package__setup_local
    #     ),
    #     context=context,
    # )
