from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="sql",
    type=str,
    required=True,
    description="SQL command to execute",
)
@option(
    name="service",
    type=str,
    required=False,
    description="DB service name (defaults to service.db.main)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Execute a SQL command in the DB container")
def app__db__exec(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    sql: str,
    service: str | None = None,
) -> AbstractResponse:
    service_name = service or app_workdir.get_main_db_service()
    if not service_name:
        raise RuntimeError("No DB service configured (service.db.main)")

    cmd_name = f"@{service_name}::db/exec"
    request = context.kernel._get_command_request_class()(
        kernel=context.kernel,
        name=cmd_name,
        arguments={
            "app_path": str(app_workdir.get_path()),
            "sql": sql,
        },
    )
    return context.kernel.execute_kernel_command(request)
