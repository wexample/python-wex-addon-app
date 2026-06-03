from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.webhook.const import WEBHOOK_LISTEN_PORT_DEFAULT

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Show webhook daemon status and registered commands for this app",
)
def app__webhook__status(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
):
    from wexample_app.response.table_response import TableResponse

    from wexample_wex_core.addons.system.helpers import system_find_process_by_port

    port = WEBHOOK_LISTEN_PORT_DEFAULT

    # ---- daemon status -------------------------------------------------------
    proc = system_find_process_by_port(port)
    if proc:
        from datetime import datetime

        started = datetime.fromtimestamp(proc.create_time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        context.io.log(
            f"Daemon: @green{{running}} — pid {proc.pid}, port {port}, started {started}"
        )
    else:
        context.io.log(f"Daemon: @red{{stopped}} — no process on port {port}")

    # ---- webhook commands in this app ----------------------------------------
    all_webhook = context.kernel.get_configuration_registry().get_webhook_commands()
    webhook_commands = [
        cmd["command"] for cmd in all_webhook.values() if cmd["command"].startswith(".")
    ]

    if not webhook_commands:
        return "No @webhook commands found in this app."

    # ---- token status --------------------------------------------------------
    tokens: dict = app_workdir.get_local_data("webhook_tokens")

    rows = []
    for cmd in sorted(webhook_commands):
        has_token = cmd in tokens
        token_status = "@green{yes}" if has_token else "@red{no}"
        rows.append([cmd, token_status])

    return TableResponse(
        kernel=context.kernel,
        content=rows,
        headers=["Command", "Token"],
    )
