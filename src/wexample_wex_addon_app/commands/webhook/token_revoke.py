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
    "command_name",
    type=str,
    required=False,
    default=None,
    description="App command whose token should be revoked, e.g. '.ping/pong'",
)
@option(
    "all",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description="Revoke tokens for all @webhook commands in this app",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON, description="Revoke the webhook token for an app command"
)
def app__webhook__token_revoke(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str | None = None,
    all: bool = False,
):
    from wexample_app.response.failure_response import FailureResponse

    if not command_name and not all:
        return FailureResponse(
            kernel=context.kernel,
            message="Specify --command-name <cmd> or --all.",
        )
    if command_name and all:
        return FailureResponse(
            kernel=context.kernel,
            message="--command-name and --all are mutually exclusive.",
        )

    if all:
        webhook_cmds = (
            context.kernel.get_configuration_registry().get_webhook_commands()
        )
        targets = [
            cmd["command"]
            for cmd in webhook_cmds.values()
            if cmd["command"].startswith(".")
        ]
        if not targets:
            return "No @webhook app commands found."
    else:
        targets = [command_name]

    for cmd in targets:
        existing = app_workdir.get_local_data_value("webhook_tokens", cmd)
        if not existing:
            context.io.warning(f"No token found for {cmd} — skipping.")
            continue
        app_workdir.delete_local_data_value("webhook_tokens", cmd)
        context.io.log(f"Token revoked for {cmd}.")
