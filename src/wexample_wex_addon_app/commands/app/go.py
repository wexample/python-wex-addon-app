from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.decorator.require_app_config import require_app_config
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


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
@require_app_config(
    path="docker.main_container",
    type=str,
    # Lambda defers resolution: the body is evaluated at call time, by which
    # point `_available_containers` (defined below in this module by the
    # codebase's "private helpers at end" convention) is in scope.
    values=lambda app_workdir: _available_containers(app_workdir),
    description="Main Docker container to enter",
    ask_question="Which container do you want to enter?",
    on_missing="ask",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Enter into the main app container interactively",
)
def app__app__go(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    container_name: str | None = None,
    user: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )
    from wexample_helpers.helpers.docker import docker_container_is_running

    container = container_name or app_workdir.get_main_container_name()
    long_name = app_workdir.docker_build_long_container_name(container)
    shell = app_workdir.get_service_shell()

    if not docker_container_is_running(long_name):
        from wexample_wex_core.resolver.addon_command_resolver import (
            AddonCommandResolver,
        )

        from wexample_wex_addon_app.commands.app.start import app__app__start

        context.io.error(f"Container @magenta{{{long_name}}} is not running.")
        context.io.suggestions(
            message=f"You may want to start the application.",
            suggestions=[
                AddonCommandResolver.build_command_from_function(app__app__start)
            ],
        )

        return None

    context.io.info(f"Entering container @magenta{{{long_name}}}...")

    docker_command = ["docker", "exec", "-ti"]
    if user:
        docker_command += ["-u", user]
    docker_command += [long_name, shell]

    return InteractiveShellCommandResponse(
        kernel=context.kernel,
        content=docker_command,
    )


def _available_containers(app_workdir: ManagedWorkdir) -> list[str]:
    import yaml
    from wexample_app.const.globals import WORKDIR_SETUP_DIR

    compose_path = (
        app_workdir.get_path()
        / WORKDIR_SETUP_DIR
        / "tmp"
        / "docker-compose.runtime.yml"
    )
    if not compose_path.exists():
        return []
    with open(compose_path) as f:
        compose = yaml.safe_load(f) or {}
    return list((compose.get("services", {}) or {}).keys())
