from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
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
    tags=[
        DomainTag.APP_LIFECYCLE,
        EffectTag.SUBPROCESS_SPAWN,
        AudienceTag.HUMAN_ONLY,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__app__go(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    container_name: str | None = None,
    user: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.failure_response import FailureResponse
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )
    from wexample_app.response.multiple_response import MultipleResponse
    from wexample_app.response.suggestions_response import SuggestionsResponse
    from wexample_helpers.helper.docker import docker_container_is_running

    container = container_name or app_workdir.get_main_container_name()
    long_name = app_workdir.docker_build_long_container_name(container)
    shell = app_workdir.get_service_shell()

    if not docker_container_is_running(long_name):
        from wexample_wex_core.resolver.addon_command_resolver import (
            AddonCommandResolver,
        )

        from wexample_wex_addon_app.commands.app.start import app__app__start

        start_command = AddonCommandResolver.build_command_from_function(
            app__app__start
        )
        return MultipleResponse(
            kernel=context.kernel,
            responses=[
                FailureResponse(
                    kernel=context.kernel,
                    message=f"Container @magenta{{{long_name}}} is not running.",
                ),
                SuggestionsResponse(
                    kernel=context.kernel,
                    message="You may want to start the application.",
                    suggestions=[start_command],
                ),
            ],
        )

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
    from wexample_app.const.globals import WORKDIR_SETUP_DIR

    from wexample_wex_addon_app.item.file.docker_compose_yaml_file import (
        DockerComposeYamlFile,
    )

    compose_path = (
        app_workdir.get_path()
        / WORKDIR_SETUP_DIR
        / "tmp"
        / "docker-compose.runtime.yml"
    )
    if not compose_path.exists():
        return []
    return list(
        DockerComposeYamlFile.create_from_path(path=compose_path).read_services().keys()
    )
