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
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="key",
    short_name="k",
    type=str,
    required=True,
    description="Variable name",
)
@option(
    name="value",
    short_name="v",
    type=str,
    required=True,
    description="Variable value",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Set a variable in .wex/local/env.yml",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.ENV,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__env__var_set(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    key: str,
    value: str,
) -> SuccessResponse:
    from wexample_app.response.success_response import SuccessResponse

    app_workdir.set_env_parameters({key: value})
    return SuccessResponse(kernel=context.kernel, message=f"{key} set")
