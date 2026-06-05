from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Remove stopped apps from the registry and update /etc/hosts",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DNS,
        DomainTag.NETWORK,
        DomainTag.SYSTEM,
        EffectTag.DESTRUCTIVE,
        EffectTag.WRITE,
        AudienceTag.DANGEROUS,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__host__clean(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_wex_addon_app.commands.host.update import app__host__update
    from wexample_wex_addon_app.common.app_registry import registry_purge_stopped

    registry_purge_stopped()
    context.io.log("Registry purged")

    return context.kernel.run_function(
        app__host__update, {"app_path": str(app_workdir.get_path())}
    )
