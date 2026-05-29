from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Deploy a published version of the app on the current host: "
        "pull images, run pre-hook, git pull, restart, run post-hook, prune."
    ),
)
def app__release__deploy(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.const.env import ENV_NAME_LOCAL
    from wexample_app.const.globals import APP_PATH_TMP
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.commands.app.restart import app__app__restart

    app_path = app_workdir.get_path()
    tmp_dir = app_path / APP_PATH_TMP
    compose_file = str(tmp_dir / "docker-compose.runtime.yml")
    docker_env_file = str(tmp_dir / "docker.env")

    def _pull(previous_value=None) -> InteractiveShellCommandResponse:
        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=[
                "docker",
                "compose",
                "--env-file",
                docker_env_file,
                "-f",
                compose_file,
                "pull",
            ],
        )

    def _hook_pre(previous_value=None) -> None:
        app_workdir.manager_run(
            cmd=[".release/deploy-pre", "--ignore-missing-command"]
        )

    def _git_pull(previous_value=None) -> InteractiveShellCommandResponse:
        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=["git", "pull", "--ff-only"],
            workdir=str(app_path),
        )

    def _restart(previous_value=None) -> AbstractResponse:
        return context.kernel.run_function(
            app__app__restart, arguments={"fast": True}
        )

    def _hook_post(previous_value=None) -> None:
        app_workdir.manager_run(
            cmd=[".release/deploy-post", "--ignore-missing-command"]
        )

    def _prune(previous_value=None) -> InteractiveShellCommandResponse | None:
        if app_workdir.get_app_env() == ENV_NAME_LOCAL:
            context.io.log("Local env — skipping docker system prune.")
            return None
        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=["docker", "system", "prune", "-a", "-f"],
        )

    return QueuedCollectionResponse(
        kernel=context.kernel,
        content=[
            _pull,
            _hook_pre,
            _git_pull,
            _restart,
            _hook_post,
            _prune,
        ],
    )
