from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="name",
    type=str,
    required=False,
    description="Name of the image to delete (as defined in builds.yml)",
)
@option(
    name="all",
    type=bool,
    is_flag=True,
    required=False,
    description="Delete all images defined in builds.yml",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Delete one or all local Docker images defined in builds.yml",
)
def app__image__delete(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    name: str | None = None,
    all: bool = False,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )
    from wexample_app.response.shell_command_response import ShellCommandResponse

    from wexample_wex_addon_app.helpers.image_builds import (
        load_builds,
        resolve_build_order,
    )

    if not name and not all:
        raise ValueError("Specify --name <image> or --all")
    if name and all:
        raise ValueError("--name and --all are mutually exclusive")

    app_path = app_workdir.get_path()
    builds = load_builds(app_path)

    if name:
        if name not in builds:
            raise KeyError(f"Build '{name}' not found in builds.yml")
        targets = [name]
    else:
        # Delete in reverse dependency order: dependents before base images
        targets = list(reversed(resolve_build_order(builds, None)))

    steps = []
    for build_name in targets:
        tag = builds[build_name]["tag"]

        def _step(
            previous_value=None,
            _tag=tag,
            _build_name=build_name,
        ) -> ShellCommandResponse:
            context.io.log(f"Deleting image: {_build_name} ({_tag})")
            return ShellCommandResponse(
                kernel=context.kernel,
                content=["docker", "rmi", "-f", _tag],
            )

        steps.append(_step)

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
