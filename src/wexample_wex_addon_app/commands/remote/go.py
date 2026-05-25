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
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Open an interactive SSH shell on the remote, cd'd into the app path",
)
def app__remote__go(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    env: str,
    name: str | None = None,
    user: str | None = None,
) -> int:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    remote = remote_resolve(
        app_workdir=app_workdir, env=env, name=name, user_override=user
    )

    target = f"{remote['user']}@{remote['host']}"
    remote_cmd = f'cd {remote["path"]} 2>/dev/null || cd /var/www; exec "$SHELL" -l'

    context.io.log(f"SSH → {target}  (cd {remote['path']})")

    return subprocess.run(["ssh", "-t", target, remote_cmd]).returncode
