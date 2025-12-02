from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir


@option(
    name="env",
    type=str,
    default=None,
    description="Indicate to use environment-specific installation (e.g. local editable packages)",
)
@option(
    name="force",
    type=bool,
    default=False,
    description="Force reinstallation of all packages",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Install package manager into suite or packages",
)
def app__setup__install(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
    env: str | None = None,
    force: bool = False,
) -> None:
    app_workdir.setup_install(env=env, force=force)
