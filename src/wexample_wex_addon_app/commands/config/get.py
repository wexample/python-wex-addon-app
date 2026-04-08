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
    description="Dot-separated key path (e.g. docker.db.main)",
)
@option(
    name="default",
    type=str,
    required=False,
    description="Default value if key is not found",
)
@option(
    name="runtime",
    type=bool,
    is_flag=True,
    required=False,
    description="Search in runtime config instead of config.yml",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Get a configuration value from config.yml")
def app__config__get(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    key: str,
    default: str | None = None,
    runtime: bool = False,
) -> str | None:
    config = app_workdir.get_runtime_config() if runtime else app_workdir.get_config()
    value = config.search(key)

    if value.is_none():
        return default

    return value.get_str_or_none()
