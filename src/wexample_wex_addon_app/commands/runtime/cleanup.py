from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@command(
    type=COMMAND_TYPE_ADDON,
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.SYSTEM,
        EffectTag.DESTRUCTIVE,
        EffectTag.WRITE,
        AudienceTag.DANGEROUS,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__runtime__cleanup(context: ExecutionContext) -> SuccessResponse:
    from wexample_app.response.success_response import SuccessResponse

    removed_containers, removed_images = context.workdir.runtime_cleanup()

    if not removed_containers and not removed_images:
        return SuccessResponse(kernel=context.kernel, message="Nothing to clean up.")
    return SuccessResponse(
        kernel=context.kernel,
        message=f"Cleaned up {removed_containers} container(s) and {removed_images} image(s).",
    )
