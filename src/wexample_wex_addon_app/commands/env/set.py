from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="environment",
    type=str,
    required=True,
    description="Environment name (local, dev, test, prod)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Set APP_ENV value in .wex/.env")
def app__env__set(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    environment: str,
) -> bool:
    import pathlib

    app_workdir.set_app_env(environment)
    context.io.log(f'Environment set to "{environment}"')

    www_dir = pathlib.Path("/var/www") / environment
    if not www_dir.exists():
        try:
            www_dir.mkdir(parents=True, exist_ok=True)
            context.io.log(f"Created {www_dir}")
        except PermissionError:
            context.io.warning(f"Could not create {www_dir} — run as root if needed")

    return True
