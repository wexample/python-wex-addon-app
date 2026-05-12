from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.decorator.require_app_config import require_app_config
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="force", type=bool, default=False, is_flag=True)
@as_sudo()
@require_app_config(
    path="git.publication_strategy",
    type=str,
    values=["main_push", "branch_merge"],
    description="Publication strategy",
    ask_question="Which publication strategy should be used for this app?",
    on_missing="ask",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish a new version of the app.",
)
def app__release__publish(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    force: bool = False,
) -> None:
    if hasattr(app_workdir, "release"):
        app_workdir.release(force=force, interactive=False)
    else:
        app_workdir._run_build_if_present()
