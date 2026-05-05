from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="key",
    short_name="k",
    type=str,
    required=True,
    description="Variable name",
)
@option(
    name="value",
    short_name="v",
    type=str,
    required=True,
    description="Variable value",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Set a variable in .wex/.env",
)
def app__env__var_set(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    key: str,
    value: str,
) -> None:
    app_workdir.set_env_parameters({key: value})
    context.io.log(f"{key} set")
