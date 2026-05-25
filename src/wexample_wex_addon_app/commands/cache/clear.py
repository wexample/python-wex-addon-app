from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__cache__clear(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    app_workdir.clear_runtime_config_cache()
    app_workdir.clear_logs()
    context.io.success("Cache cleared.")
