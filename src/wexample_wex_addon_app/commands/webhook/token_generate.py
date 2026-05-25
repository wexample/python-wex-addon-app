from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    "command_name",
    type=str,
    required=False,
    default=None,
    description="App command to secure, e.g. '.ping/pong'",
)
@option(
    "all",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description="Generate tokens for all @webhook commands in this app",
)
@option(
    "force",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description="Revoke existing token and generate a new one",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Generate and store a webhook token for an app command",
)
def app__webhook__token_generate(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str | None = None,
    all: bool = False,
    force: bool = False,
) -> None:
    if not command_name and not all:
        context.io.error("Specify --command-name <cmd> or --all.")
        return
    if command_name and all:
        context.io.error("--command-name and --all are mutually exclusive.")
        return

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
            context.io.log("No @webhook app commands found.")
            return
    else:
        targets = [command_name]

    for cmd in targets:
        _generate_one(context, app_workdir, cmd, force)


def _generate_one(context, app_workdir, command_name: str, force: bool) -> None:
    existing = app_workdir.get_local_data_value("webhook_tokens", command_name)
    if existing:
        if not force:
            context.io.warning(
                f"Token already exists for {command_name} — skipping (use --force)."
            )
            return
        app_workdir.delete_local_data_value("webhook_tokens", command_name)

    token = app_workdir.rotate_local_token("webhook_tokens", command_name)
    context.io.log(f"Token generated for {command_name}:  @yellow{{{token}}}")
