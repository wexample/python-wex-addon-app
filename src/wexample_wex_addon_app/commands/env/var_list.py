from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="List all variables defined in .wex/local/env.yml",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.ENV,
        EffectTag.READ_ONLY,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__env__var_list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
):
    from wexample_app.response.properties_response import PropertiesResponse

    env_vars = app_workdir.get_env_parameters().to_dict()
    if not env_vars:
        return "No variables found in .wex/local/env.yml"
    return PropertiesResponse(
        kernel=context.kernel,
        properties=dict(sorted(env_vars.items())),
        title=".wex/local/env.yml",
    )
