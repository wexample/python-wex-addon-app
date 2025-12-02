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
    from wexample_app.response.boolean_response import BooleanResponse
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="force",
    type=bool,
    default=False,
    is_flag=True,
    description="Force bump even if package has no new content",
)
@option(name="yes", type=bool, default=False, is_flag=True)
@middleware(middleware=SuiteOrEachPackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version only if package has new content (HEAD not tagged). Use --force to bump regardless of changes. Use --all-packages to bump all packages, --packages-only to exclude suite, --suite-only to exclude packages.",
)
def app__package__bump(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
    yes: bool = False,
    force: bool = False,
) -> BooleanResponse:
    from wexample_app.response.boolean_response import BooleanResponse

    package_name = app_workdir.get_package_name()
    bumped = app_workdir.bump(interactive=not yes, force=force)

    if bumped:
        context.io.success(f"Successfully bumped {package_name}.")
    else:
        context.io.log(f"Bump aborted for {package_name}.")

    return BooleanResponse(kernel=context.kernel, content=bumped)
