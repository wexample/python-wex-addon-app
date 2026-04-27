from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.const.app import SIDECAR_LIST

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="name",
    short_name="n",
    type=str,
    required=True,
    description="Sidecar short name (e.g. proxy)",
)
@option(
    name="env",
    short_name="e",
    type=str,
    required=False,
    description="Environment (defaults to local)",
)
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Start a sidecar app")
def app__sidecar__start(
    context: ExecutionContext,
    name: str,
    env: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    if name not in SIDECAR_LIST:
        raise ValueError(
            f"Unknown sidecar '{name}'. Expected one of: {', '.join(SIDECAR_LIST)}"
        )

    env = env or "local"
    app_addon_manager = AppAddonManager.from_kernel(context.kernel)
    sidecar_path = app_addon_manager.get_sidecar_path(name=name, env=env)

    def _create(previous_value=None) -> None:
        if sidecar_path.exists():
            import shutil

            from wexample_app.response.queue_collection.queued_collection_stop_response import (
                QueuedCollectionStopResponse,
            )

            from wexample_wex_addon_app.commands.app.started import (
                APP_STARTED_CHECK_MODE_ANY_CONTAINER,
                _check_started,
            )

            sidecar_workdir = app_addon_manager.create_app_workdir(path=sidecar_path)
            if sidecar_workdir and _check_started(
                sidecar_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context
            ):
                return QueuedCollectionStopResponse(
                    kernel=context.kernel,
                    reason=f"Sidecar '{name}' already running",
                )

            shutil.rmtree(sidecar_path)

        from wexample_wex_addon_app.commands.app.init import app__app__init

        context.kernel.run_function(
            app__app__init,
            {
                "app_path": str(sidecar_path),
                "env": env,
                "name": f"wex-{name}",
                "services": [name],
            },
        )

        context.io.log(f"Sidecar '{name}' app created at {sidecar_path}")

    def _start(previous_value=None):
        from wexample_wex_addon_app.commands.app.start import app__app__start

        return context.kernel.run_function(
            app__app__start, {"app_path": str(sidecar_path)}
        )

    return QueuedCollectionResponse(kernel=context.kernel, content=[_create, _start])
