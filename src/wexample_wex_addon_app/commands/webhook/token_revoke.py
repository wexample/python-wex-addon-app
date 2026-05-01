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
    "command_name",
    type=str,
    required=True,
    description="App command whose token should be revoked, e.g. '.ping/pong'",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Revoke the webhook token for an app command")
def app__webhook__token_revoke(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str,
) -> None:
    existing = app_workdir.get_local_data_value("webhook_tokens", command_name)
    if not existing:
        context.io.warning(f"No token found for {command_name}.")
        return

    app_workdir.delete_local_data_value("webhook_tokens", command_name)
    context.io.log(f"Token revoked for {command_name}.")
