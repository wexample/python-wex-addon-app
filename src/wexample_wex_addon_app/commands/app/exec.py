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
    name="command",
    type=str,
    required=True,
    description="Command to execute inside the container",
)
@option(
    name="user",
    type=str,
    required=False,
    description="User name or uid to run as",
)
@option(
    name="interactive",
    type=bool,
    is_flag=True,
    required=False,
    description="Open an interactive TTY",
)
@option(
    name="ignore_error",
    type=bool,
    is_flag=True,
    required=False,
    description="Do not fail on non-zero exit code",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Execute a command inside an app container")
def app__app__exec(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    command: str,
    container_name: str | None = None,
    user: str | None = None,
    interactive: bool = False,
    ignore_error: bool = False,
) -> AbstractResponse:
    from wexample_app.response.shell_command_response import ShellCommandResponse

    container = container_name or app_workdir.get_main_container_name()
    long_name = app_workdir.docker_build_long_container_name(container)
    shell = app_workdir.get_service_shell()

    docker_command = ["docker", "exec"]

    if interactive:
        docker_command += ["-ti"]

    if user:
        docker_command += ["-u", user]

    # v6: todo — appeler le hook @service::hook/exec pour injecter des commandes préalables
    #             (ex: charger l'env du service avant d'exécuter). Bloqué par migration des services.

    # v6: todo — --sync : distinguer "capturer la sortie" vs "juste exécuter" (NonInteractiveShellCommandResponse)
    #             actuellement tout passe par ShellCommandResponse (capture).

    # v6: todo — args_parse_one : parser intelligemment --command (string ou liste imbriquée)

    if interactive:
        docker_command += [long_name, command]
        from wexample_app.response.interactive_shell_command_response import InteractiveShellCommandResponse
        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=docker_command,
        )

    docker_command += [long_name, shell, "-c", command]

    return ShellCommandResponse(
        kernel=context.kernel,
        content=docker_command,
        ignore_error=ignore_error,
    )
