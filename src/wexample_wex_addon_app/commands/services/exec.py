from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.dict_response import DictResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app. import ManagedWorkdir


@option(
    name="hook",
    short_name="h",
    type=str,
    required=True,
    description="Service hook to execute for all installed services (e.g. service/ready)",
)
@option(
    name="arguments",
    type=str,
    required=False,
    description='Optional dict-like arguments string, e.g. \'{"foo": "bar"}\'',
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Execute a hook for all installed services")
def app__services__exec(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    hook: str,
    arguments: str | None = None,
) -> DictResponse:
    from wexample_app.response.dict_response import DictResponse
    from wexample_helpers.helpers.args import args_parse_dict

    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    app_addon_manager = AppAddonManager.from_kernel(context.kernel)
    results = app_addon_manager.run_service_hook(
        hook=hook,
        app_workdir=app_workdir,
        arguments=args_parse_dict(arguments) if arguments else None,
    )

    return DictResponse(kernel=context.kernel, content=results)
