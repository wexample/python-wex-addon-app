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
@command(
    type=COMMAND_TYPE_ADDON,
    description="List all webhook tokens registered for this app",
)
def app__webhook__token_list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    tokens: dict = app_workdir.get_local_data("webhook_tokens")

    if not tokens:
        context.io.log("No webhook tokens registered for this app.")
        return

    rows = [
        [cmd, f"@yellow{{{token[:8]}}}..."] for cmd, token in sorted(tokens.items())
    ]

    context.io.table(data=rows, headers=["Command", "Token (prefix)"])
