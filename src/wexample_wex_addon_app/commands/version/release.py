from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="force", type=bool, default=False, is_flag=True)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to package manager (npm, PyPI, packagist, etc.).",
)
def app__version__release(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
    yes: bool = False,
    force: bool = False,
) -> None:
    app_workdir.release(
        interactive=not yes,
        force=force,
    )
