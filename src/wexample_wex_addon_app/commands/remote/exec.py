from __future__ import annotations

import subprocess
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
    name="command",
    short_name="c",
    type=str,
    required=True,
    description="Shell command to execute on the remote",
)
@option(
    name="env",
    short_name="e",
    type=str,
    required=True,
    description="Target environment",
)
@option(
    name="name",
    type=str,
    required=False,
    default=None,
    description="Remote name (omit to use the first one)",
)
@option(
    name="user",
    type=str,
    required=False,
    default=None,
    description="Override SSH user (otherwise remote.user, otherwise $USER)",
)
@option(
    name="cd",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description="cd into the app path before executing the command",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Execute a command on the remote via SSH",
)
def app__remote__exec(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command: str,
    env: str,
    name: str | None = None,
    user: str | None = None,
    cd: bool = False,
) -> int:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    remote = remote_resolve(
        app_workdir=app_workdir, env=env, name=name, user_override=user
    )

    target = f"{remote['user']}@{remote['host']}"
    remote_cmd = f"cd {remote['path']} && {command}" if cd else command

    context.io.log(f"SSH exec → {target}: {remote_cmd}")

    return subprocess.run(["ssh", target, remote_cmd]).returncode
