from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Fix app file permissions and ownership")
def app__app__perms(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
) -> None:
    from wexample_filestate.enum.scopes import Scope
    from wexample_filestate.item.abstract_item_target import AbstractItemTarget

    AbstractItemTarget.apply(
        app_workdir,
        interactive=False,
        scopes={Scope.PERMISSIONS, Scope.OWNERSHIP},
    )
    context.io.log("Permissions applied")
