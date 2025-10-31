from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.commands.file_state.rectify import app__file_state__rectify
from wexample_wex_addon_app.commands.package.bump import app__package__bump
from wexample_wex_addon_app.commands.package.commit_and_push import app__package__commit_and_push
from wexample_wex_addon_app.commands.package.publish import app__package__publish
from wexample_wex_addon_app.commands.version.propagate import app__version__propagate
from wexample_wex_addon_app.middleware.package_suite_middleware import PackageSuiteMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import FrameworkPackageSuiteWorkdir
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
        app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    app_workdir.packages_validate_internal_dependencies_declarations()

    # Process packages in order leaf -> trunk.
    # Use manager for every command allow to use complete specific environment.
    for package in app_workdir.get_ordered_packages():
        package.manager_run_command(
            command=app__package__bump
        )

        package.manager_run_command(
            command=app__file_state__rectify
        )

        package.manager_run_command(
            command=app__package__commit_and_push()
        )

        package.manager_run_command(
            command=app__version__propagate
        )

        package.manager_run_command(
            command=app__package__publish
        )
