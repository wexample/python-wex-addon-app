from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="env",
    type=str,
    required=False,
    description="Environment (defaults to local)",
)
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Stop the proxy helper app")
def app__helper__stop(
    context: ExecutionContext,
    env: str | None = None,
) -> AbstractResponse:
    from pathlib import Path

    env = env or "local"
    proxy_path = Path(f"/var/www/{env}/wex-proxy")

    from wexample_wex_addon_app.commands.app.stop import app__app__stop

    return context.kernel.run_function(
        app__app__stop,
        {"app_path": str(proxy_path)},
    )
