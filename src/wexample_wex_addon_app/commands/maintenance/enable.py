from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Anchor command: activate maintenance mode on the app. Services and apps "
        "plug their own behavior via @attach (e.g. laravel → `php artisan down`)."
    ),
)
def app__maintenance__enable(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> None:
    context.io.log("Maintenance enabled")
