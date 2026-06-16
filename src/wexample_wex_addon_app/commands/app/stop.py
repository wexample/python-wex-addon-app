from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="force",
    type=bool,
    is_flag=True,
    required=False,
    description="Skip started check and stop containers regardless of runtime state",
)
@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Stop the app containers",
    tags=[
        DomainTag.APP_LIFECYCLE,
        EffectTag.DESTRUCTIVE,
        EffectTag.WRITE,
        AudienceTag.DANGEROUS,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__app__stop(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    force: bool = False,
) -> AbstractResponse:
    from wexample_app.const.globals import APP_PATH_TMP
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )
    from wexample_app.response.shell_command_response import ShellCommandResponse

    app_path = app_workdir.get_path()
    tmp_dir = app_path / APP_PATH_TMP
    compose_file = str(tmp_dir / "docker-compose.runtime.yml")
    docker_env_file = str(tmp_dir / "docker.env")

    def _checkup(previous_value=None):
        from wexample_app.response.queue_collection.queued_collection_stop_response import (
            QueuedCollectionStopResponse as QueuedCollectionStop,
        )

        runtime = app_workdir.get_runtime_config()
        if not runtime.search("app.started").get_bool_or_default(False):
            return QueuedCollectionStop(
                kernel=context.kernel, reason="App already stopped"
            )
        return True

    def _stop(previous_value=None) -> ShellCommandResponse:
        return ShellCommandResponse(
            kernel=context.kernel,
            content=[
                "docker",
                "compose",
                "--env-file",
                docker_env_file,
                "-f",
                compose_file,
                "stop",
            ],
        )

    def _rm(previous_value=None) -> ShellCommandResponse:
        return ShellCommandResponse(
            kernel=context.kernel,
            content=[
                "docker",
                "compose",
                "--env-file",
                docker_env_file,
                "-f",
                compose_file,
                "rm",
                "-f",
            ],
        )

    def _complete(previous_value=None) -> None:
        import json as _json

        from wexample_wex_addon_app.commands.host.update import app__host__update
        from wexample_wex_addon_app.common.app_registry import registry_unregister_app

        runtime_path = app_workdir.get_runtime_config_file().get_path()
        if runtime_path.exists():
            with open(runtime_path) as f:
                _data = _json.load(f) or {}
            _data.setdefault("app", {})["started"] = False
            with open(runtime_path, "w") as f:
                _json.dump(_data, f)
        registry_unregister_app(app_workdir)
        context.kernel.run_function(app__host__update, {"app_path": str(app_path)})

    steps = [_stop, _rm, _complete] if force else [_checkup, _stop, _rm, _complete]
    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
