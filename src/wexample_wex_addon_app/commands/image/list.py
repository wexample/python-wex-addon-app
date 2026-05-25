from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="List all local Docker images defined in builds.yml",
)
def app__image__list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    import subprocess

    from wexample_app.response.null_response import NullResponse

    from wexample_wex_addon_app.helpers.image_builds import load_builds

    app_path = app_workdir.get_path()
    builds = load_builds(app_path)

    rows = []
    for build_name, build in builds.items():
        tag = build["tag"]
        result = subprocess.run(
            [
                "docker",
                "images",
                "--format",
                "{{.ID}}\t{{.Size}}\t{{.CreatedSince}}",
                tag,
            ],
            capture_output=True,
            text=True,
        )
        line = result.stdout.strip()
        if line:
            image_id, size, created = line.split("\t", 2)
        else:
            image_id, size, created = "—", "—", "not built"

        rows.append((build_name, tag, image_id, size, created))

    if not rows:
        context.io.log("No builds defined in builds.yml")
        return NullResponse(kernel=context.kernel)

    col_name = max(len(r[0]) for r in rows)
    col_tag = max(len(r[1]) for r in rows)

    header = f"{'NAME':<{col_name}}  {'TAG':<{col_tag}}  {'IMAGE ID':<12}  {'SIZE':<10}  CREATED"
    separator = "-" * len(header)
    context.io.log(header)
    context.io.log(separator)
    for build_name, tag, image_id, size, created in rows:
        context.io.log(
            f"{build_name:<{col_name}}  {tag:<{col_tag}}  {image_id:<12}  {size:<10}  {created}"
        )

    return NullResponse(kernel=context.kernel)
