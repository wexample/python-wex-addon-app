from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Commit and push changes for a package.",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.PACKAGE,
        DomainTag.RELEASE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
        ScopeTag.REMOTE,
    ],
)
def app__version__push(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
) -> SuccessResponse:
    from wexample_app.response.success_response import SuccessResponse

    package_name = app_workdir.get_package_name()
    app_workdir.commit_changes()
    app_workdir.push_to_deployment_remote()
    return SuccessResponse(kernel=context.kernel, message=f"Pushed {package_name}.")
