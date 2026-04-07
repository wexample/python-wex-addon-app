from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_SERVICE
from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext
    from wexample_wex_addon_app.service.app_service import AppService


@command(type=COMMAND_TYPE_SERVICE, description="Contribute domains_string to runtime config")
def letsencrypt__runtime__contribution(
        context: ExecutionContext,
        service: AppService,
) -> AbstractResponse:
    from wexample_app.response.dict_response import DictResponse

    # domains_string is now computed by config/write — nothing to contribute here
    return DictResponse(kernel=context.kernel, content={})
