from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="key",
    type=str,
    required=True,
    description="Dot-separated key path (e.g. docker.main_db_container)",
)
@option(
    name="value",
    type=str,
    required=True,
    description="Value to set",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Set a configuration value in config.yml")
def app__config__set(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    key: str,
    value: str,
) -> None:
    app_workdir.get_config_file().write_config_value(key, value)
    context.io.log(f"Set {key} = {value}")
