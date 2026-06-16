from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="tail",
    type=int,
    required=False,
    default=100,
    description="Number of log lines to display before following",
)
@option(
    name="container_name",
    type=str,
    required=False,
    description="Container name (defaults to main container)",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Follow container logs",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.LOG,
        EffectTag.LONG_RUNNING,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__log__follow(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    tail: int = 100,
    container_name: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )

    long_name = app_workdir.docker_build_long_container_name(
        container_name or app_workdir.get_main_container_name()
    )

    return InteractiveShellCommandResponse(
        kernel=context.kernel,
        content=[
            "docker",
            "logs",
            long_name,
            "--tail",
            str(tail),
            "-f",
        ],
    )
