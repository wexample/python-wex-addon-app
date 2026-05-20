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
@command(type=COMMAND_TYPE_ADDON, description="Stop a sidecar app")
def app__sidecar__stop(
    context: ExecutionContext,
    name: str,
    env: str | None = None,
) -> AbstractResponse:
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager
    from wexample_wex_addon_app.commands.app.stop import app__app__stop

    if name not in SIDECAR_LIST:
        raise ValueError(
            f"Unknown sidecar '{name}'. Expected one of: {', '.join(SIDECAR_LIST)}"
        )

    env = env or "local"
    sidecar_path = AppAddonManager.get_sidecar_path(name=name, env=env)

    return context.kernel.run_function(
        app__app__stop,
        {"app_path": str(sidecar_path)},
    )
