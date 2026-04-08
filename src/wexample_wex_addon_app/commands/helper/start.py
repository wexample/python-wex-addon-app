from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

from wexample_wex_addon_app.const.app import HELPER_APPS_LIST


@option(
    name="name",
    type=str,
    required=True,
    description="Helper app short name (e.g. proxy)",
)
@option(
    name="env",
    type=str,
    required=False,
    description="Environment (defaults to local)",
)
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Start a helper app")
def app__helper__start(
    context: ExecutionContext,
    name: str,
    env: str | None = None,
) -> AbstractResponse:
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    if name not in HELPER_APPS_LIST:
        raise ValueError(
            f"Unknown helper app '{name}'. Expected one of: {', '.join(HELPER_APPS_LIST)}"
        )

    env = env or "local"
    app_addon_manager = AppAddonManager.from_kernel(context.kernel)
    helper_path = app_addon_manager.get_helper_app_path(name=name, env=env)

    def _create(previous_value=None) -> None:
        if helper_path.exists():
            import shutil

            from wexample_wex_addon_app.commands.app.started import (
                APP_STARTED_CHECK_MODE_ANY_CONTAINER,
                _check_started,
            )

            helper_workdir = app_addon_manager.create_app_workdir(path=helper_path)
            if helper_workdir and _check_started(
                helper_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context
            ):
                context.io.log(f"Helper '{name}' already running, skipping creation")
                return

            shutil.rmtree(helper_path)

        from wexample_wex_addon_app.commands.app.init import app__app__init

        context.kernel.run_function(
            app__app__init,
            {
                "app_path": str(helper_path),
                "env": env,
                "name": f"wex-{name}",
                "services": [name],
            },
        )

        context.io.log(f"Helper '{name}' app created at {helper_path}")

    def _start(previous_value=None):
        from wexample_wex_addon_app.commands.app.start import app__app__start

        return context.kernel.run_function(app__app__start, {"app_path": str(helper_path)})

    return QueuedCollectionResponse(kernel=context.kernel, content=[_create, _start])
