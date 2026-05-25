from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="key",
    short_name="k",
    type=str,
    required=True,
    description="Variable name",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Get a variable value from .wex/local/env.yml",
)
def app__env__var_get(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    key: str,
) -> str | None:
    value = app_workdir.get_env_parameter(key)
    if value is None:
        context.io.warning(f"{key} is not set")
    else:
        context.io.log(value)
    return value
