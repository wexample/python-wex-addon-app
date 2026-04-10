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

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Stop the app containers")
def app__app__stop(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
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
        # v6: todo — proxy unregister (bloqué par migration proxy)
        # v6: todo — appeler hook app/stop-post (bloqué par migration services)
        from wexample_wex_addon_app.commands.hosts.update import app__hosts__update
        from wexample_wex_addon_app.common.app_registry import registry_unregister_app

        import yaml as _yaml

        runtime_path = app_workdir.get_runtime_config_file().get_path()
        if runtime_path.exists():
            with open(runtime_path) as f:
                _data = _yaml.safe_load(f) or {}
            _data.setdefault("app", {})["started"] = False
            with open(runtime_path, "w") as f:
                _yaml.dump(_data, f)
        registry_unregister_app(context.kernel, app_workdir)
        context.kernel.run_function(app__hosts__update, {"app_path": str(app_path)})

    return QueuedCollectionResponse(kernel=context.kernel, content=[_checkup, _stop, _rm, _complete])
