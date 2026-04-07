from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="container_name",
    type=str,
    required=False,
    description="Container name (defaults to main container)",
)
@option(
    name="user",
    type=str,
    required=False,
    description="User name or uid to run as",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Enter into the main app container interactively")
def app__app__go(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    container_name: str | None = None,
    user: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.interactive_shell_command_response import InteractiveShellCommandResponse

    container = container_name or app_workdir.get_main_container_name()
    long_name = app_workdir.docker_build_long_container_name(container)
    shell = app_workdir.get_service_shell()

    docker_command = ["docker", "exec", "-ti"]
    if user:
        docker_command += ["-u", user]
    docker_command += [long_name, shell]

    return InteractiveShellCommandResponse(
        kernel=context.kernel,
        content=docker_command,
    )
