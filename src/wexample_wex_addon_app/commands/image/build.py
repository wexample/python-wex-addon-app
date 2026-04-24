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

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="name",
    type=str,
    required=False,
    description="Name of the image to build (as defined in builds.yml)",
)
@option(
    name="all",
    type=bool,
    is_flag=True,
    required=False,
    description="Build all images defined in builds.yml",
)
@option(
    name="clear_cache",
    type=bool,
    is_flag=True,
    required=False,
    description="Build without Docker layer cache",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Build one or all local Docker images defined in builds.yml",
)
def app__image__build(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    name: str | None = None,
    all: bool = False,
    clear_cache: bool = False,
) -> AbstractResponse:
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

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
    ordered = resolve_build_order(builds, name if not all else None)

    steps = []
    for build_name in ordered:
        build = builds[build_name]
        dockerfile = str(app_path / build["dockerfile"])
        tag = build["tag"]

        def _step(
            previous_value=None,
            _dockerfile=dockerfile,
            _tag=tag,
            _build_name=build_name,
        ):
            context.io.log(f"Building image: {_build_name} → {_tag}")
            cmd = ["docker", "build", "-f", _dockerfile, "-t", _tag]
            if clear_cache:
                cmd.append("--no-cache")
            cmd.append(str(app_path))
            return InteractiveShellCommandResponse(
                kernel=context.kernel, content=cmd
            )

        steps.append(_step)

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
