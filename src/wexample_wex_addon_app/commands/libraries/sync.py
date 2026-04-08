from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__libraries__sync(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    app_workdir.libraries_sync()
