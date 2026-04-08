from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir


@option(
    name="fast",
    type=bool,
    is_flag=True,
    required=False,
    description="Skip checkup and config steps, just remove containers",
)
@as_sudo()
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Stop the app containers")
def app__app__stop(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    fast: bool = False,
) -> AbstractResponse:
    from pathlib import Path

    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_app.response.shell_command_response import ShellCommandResponse
    from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP

    app_path = app_workdir.get_path()
    compose_file = str(
        app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "docker-compose.runtime.yml"
    )

    def _checkup(previous_value=None):
        # v6: todo — appeler app::app/started pour vérifier si l'app tourne
        #             actuellement on vérifie directement le runtime config
        from wexample_app.response.queue_collection.queued_collection_stop_response import QueuedCollectionStopResponse as QueuedCollectionStop
        runtime = app_workdir.get_runtime_config()
        if not runtime.search("app.started").get_bool_or_default(False):
            context.io.log("App already stopped")
            return QueuedCollectionStop(kernel=context.kernel, reason="App already stopped")
        return True

    def _stop(previous_value=None) -> ShellCommandResponse:
        # v6: todo — appeler hook app/stop-pre via @service::hook/exec (bloqué par migration services)
        return ShellCommandResponse(
            kernel=context.kernel,
            content=["docker", "compose", "-f", compose_file, "stop"],
        )

    def _rm(previous_value=None) -> ShellCommandResponse:
        return ShellCommandResponse(
            kernel=context.kernel,
            content=["docker", "compose", "-f", compose_file, "rm", "-f"],
        )

    def _complete(previous_value=None) -> None:
        # v6: todo — hosts/update + proxy unregister (bloqué par migration proxy)
        # v6: todo — appeler hook app/stop-post (bloqué par migration services)
        runtime_path = (
            app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "config.runtime.yml"
        )
        if runtime_path.exists():
            import yaml

            with open(runtime_path) as f:
                data = yaml.safe_load(f) or {}
            data.setdefault("app", {})["started"] = False
            with open(runtime_path, "w") as f:
                yaml.dump(data, f)

    if fast:
        steps = [_rm]
    else:
        steps = [_checkup, _stop, _rm, _complete]

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
