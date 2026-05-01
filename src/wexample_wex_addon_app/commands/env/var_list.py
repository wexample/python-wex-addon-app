from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="List all variables defined in .wex/.env",
)
def app__env__var_list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    env_vars = app_workdir.get_env_parameters().to_dict()
    if not env_vars:
        context.io.log("No variables found in .wex/.env")
        return
    for key, value in sorted(env_vars.items()):
        context.io.log(f"{key}={value}")
