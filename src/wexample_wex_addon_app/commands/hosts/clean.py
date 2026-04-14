from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Remove stopped apps from the registry and update /etc/hosts",
)
def app__hosts__clean(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_wex_addon_app.commands.hosts.update import app__hosts__update
    from wexample_wex_addon_app.common.app_registry import registry_purge_stopped

    registry_purge_stopped()
    context.io.log("Registry purged")

    return context.kernel.run_function(
        app__hosts__update, {"app_path": str(app_workdir.get_path())}
    )
