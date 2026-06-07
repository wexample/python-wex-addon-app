from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.list_response import ListResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="List app domains",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DNS,
        DomainTag.NETWORK,
        EffectTag.READ_ONLY,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__domain__list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> ListResponse:
    from wexample_app.response.list_response import ListResponse

    return ListResponse(
        kernel=context.kernel,
        content=app_workdir.get_domains_config().get("domains", []),
    )
