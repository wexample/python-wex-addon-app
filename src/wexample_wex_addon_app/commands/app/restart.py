from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="rebuild",
    type=bool,
    is_flag=True,
    required=False,
    description="Rebuild all Docker images (no cache) then force docker compose up --build",
)
@option(
    name="env",
    type=str,
    required=False,
    description="App environment",
)
@option(
    name="fast",
    type=bool,
    is_flag=True,
    required=False,
    description="Skip config rewrite, just stop then docker compose up (pass-through to app/start --fast)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Restart the app (stop then start)",
    tags=[
        DomainTag.APP_LIFECYCLE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__app__restart(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    rebuild: bool = False,
    env: str | None = None,
    fast: bool = False,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.commands.app.stop import app__app__stop

    def _stop(previous_value=None) -> AbstractResponse | None:
        # Skip stop entirely when the app has never started — otherwise
        # `docker compose stop` runs against a runtime compose file that may
        # reference unmaterialized services and fails. Restart on a fresh app
        # then behaves like a plain start.
        runtime = app_workdir.get_runtime_config()
        if not runtime.search("app.started").get_bool_or_default(False):
            context.io.log("App not started — skipping stop, proceeding to start.")
            return None
        return context.kernel.run_function(app__app__stop, arguments={"force": True})

    def _start(previous_value=None) -> AbstractResponse:
        from wexample_wex_addon_app.commands.app.start import app__app__start

        arguments: dict = {}
        if rebuild:
            arguments["rebuild"] = True
        if env is not None:
            arguments["env"] = env
        if fast:
            arguments["fast"] = True
        return context.kernel.run_function(app__app__start, arguments=arguments)

    return QueuedCollectionResponse(kernel=context.kernel, content=[_stop, _start])
