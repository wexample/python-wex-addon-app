from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
    EachSuitePackageMiddleware,
)
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@middleware(middleware=AppMiddleware)
@middleware(middleware=EachSuitePackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version only if package has new content (HEAD not tagged). Use --all-packages to check all packages in a suite.",
)
def app__package__bump_changed(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
    yes: bool = False,
) -> None:
    package_name = app_workdir.get_package_name()
    
    # Check if package has changes since last publication tag
    if not app_workdir.has_changes_since_last_publication_tag():
        context.io.log(f"Package {package_name} has no new content to bump.")
        return
    
    context.io.info(f"Package {package_name} has new content. Bumping version...")
    
    if app_workdir.bump(interactive=not yes):
        context.io.success(f"Successfully bumped {package_name}.")
    else:
        context.io.log(f"Bump aborted for {package_name}.")
