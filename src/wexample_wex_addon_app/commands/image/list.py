from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
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
):
    import subprocess

    from wexample_app.response.table_response import TableResponse

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

        rows.append([build_name, tag, image_id, size, created])

    if not rows:
        return "No builds defined in builds.yml"

    return TableResponse(
        kernel=context.kernel,
        content=rows,
        headers=["NAME", "TAG", "IMAGE ID", "SIZE", "CREATED"],
    )
