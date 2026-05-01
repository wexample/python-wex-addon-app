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
    description="App command to secure, e.g. '.ping/pong'",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Generate and store a webhook token for an app command")
def app__webhook__token_generate(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str,
) -> None:
    existing = app_workdir.get_local_data_value("webhook_tokens", command_name)
    if existing:
        context.io.warning(f"A token already exists for {command_name}. Use token-revoke first.")
        return

    token = app_workdir.rotate_local_token("webhook_tokens", command_name)

    context.io.log(f"Token generated for {command_name}:")
    context.io.log(f"  @yellow{{{token}}}")
    context.io.log("Store it now — it will not be shown again.")
