from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.boolean_response import BooleanResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="service",
    short_name="s",
    type=str,
    required=True,
    description="Service name",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Return true if service is installed on app",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.SERVICE,
        EffectTag.READ_ONLY,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__service__used(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    service: str,
) -> BooleanResponse:
    from wexample_app.response.boolean_response import BooleanResponse
    from wexample_helpers.helpers.string import string_to_snake_case

    service_name = string_to_snake_case(service)
    installed_services = app_workdir.get_config().search("service")
    is_used = (
        not installed_services.is_none()
        and service_name in installed_services.to_dict()
    )

    return BooleanResponse(kernel=context.kernel, content=is_used)
