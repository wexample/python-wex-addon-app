from __future__ import annotations

import shlex
import subprocess
from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="command",
    short_name="c",
    type=str,
    required=False,
    description="Shell command to execute on the remote (legacy single-string form; prefer args after `--`)",
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
    description="Execute a command on the remote via SSH. Use `-- <cmd> [args...]` to pass complex commands without shell-quoting headaches.",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.NETWORK,
        DomainTag.SSH,
        EffectTag.NETWORK_CALL,
        EffectTag.SUBPROCESS_SPAWN,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.CONTAINER,
        ScopeTag.LOCAL,
        ScopeTag.REMOTE,
    ],
)
def app__remote__exec(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    env: str,
    command: str | None = None,
    name: str | None = None,
    user: str | None = None,
    cd: bool = False,
    extra_args: list[str] | None = None,
) -> int:
    from wexample_cli.helpers.extra_args import resolve_shell_command

    from wexample_wex_addon_app.helpers.remote import remote_resolve

    remote_cmd = resolve_shell_command(
        context=context, command=command, extra_args=extra_args
    )
    if remote_cmd is None:
        from wexample_app.response.failure_response import FailureResponse

        return FailureResponse(
            kernel=context.kernel,
            message='No command provided. Pass `--command "..."` or `-- <cmd> [args...]`.',
        )

    remote = remote_resolve(
        app_workdir=app_workdir, env=env, name=name, user_override=user
    )

    target = f"{remote['user']}@{remote['host']}"
    if cd:
        remote_cmd = f"cd {shlex.quote(str(remote['path']))} && {remote_cmd}"

    context.io.log(f"SSH exec → {target}: {remote_cmd}")

    return subprocess.run(["ssh", target, remote_cmd]).returncode
