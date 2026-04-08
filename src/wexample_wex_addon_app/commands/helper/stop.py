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
@command(type=COMMAND_TYPE_ADDON, description="Stop a helper app")
def app__helper__stop(
    context: ExecutionContext,
    name: str,
    env: str | None = None,
) -> AbstractResponse:
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager
    from wexample_wex_addon_app.commands.app.stop import app__app__stop

    if name not in HELPER_APPS_LIST:
        raise ValueError(
            f"Unknown helper app '{name}'. Expected one of: {', '.join(HELPER_APPS_LIST)}"
        )

    env = env or "local"
    helper_path = AppAddonManager.get_helper_app_path(name=name, env=env)

    return context.kernel.run_function(
        app__app__stop,
        {"app_path": str(helper_path)},
    )
