from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="service",
    type=str,
    required=False,
    description="DB service name (defaults to docker.db.main)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Open an interactive DB CLI",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DB,
        EffectTag.SUBPROCESS_SPAWN,
        AudienceTag.HUMAN_ONLY,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__db__go(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    service: str | None = None,
) -> AbstractResponse:
    from wexample_helpers.helpers.string import string_to_kebab_case

    service_name = service or app_workdir.get_main_db_service()
    if not service_name:
        raise RuntimeError("No DB service configured (docker.db.main)")

    request = context.kernel._get_command_request_class()(
        kernel=context.kernel,
        name=f"@{string_to_kebab_case(service_name)}::db/go",
        arguments={"app_path": str(app_workdir.get_path())},
    )
    return context.kernel.execute_kernel_command(request)
