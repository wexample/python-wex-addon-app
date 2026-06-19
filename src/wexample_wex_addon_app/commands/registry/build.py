from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.success_response import SuccessResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.REGISTRY,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__registry__build(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> SuccessResponse:
    from wexample_app.response.success_response import SuccessResponse
    from wexample_helpers.helper.cli import cli_make_clickable_path

    registry = app_workdir.get_registry_file(rebuild=True)

    return SuccessResponse(
        kernel=context.kernel,
        message=f"Registry updated at: {cli_make_clickable_path(registry.get_path())}",
    )
