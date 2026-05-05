from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="force", type=bool, default=False, is_flag=True)
@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish a new version of the app.",
)
def app__release__publish(
    context: ExecutionContext,
    app_workdir: RepoWorkdir,
    force: bool = False,
) -> None:
    app_workdir.publish(force=force, interactive=False)
