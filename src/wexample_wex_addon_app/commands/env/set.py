from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

_WWW_ROOT = pathlib.Path("/var/www")


@option(
    name="environment",
    type=str,
    required=True,
    description="Environment name (local, dev, test, prod)",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Set APP_ENV value in .wex/local/env.yml",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.ENV,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__env__set(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    environment: str,
) -> bool:
    app_workdir.set_app_env(environment)
    context.io.log(f'Environment set to "{environment}"')

    www_dir = _WWW_ROOT / environment
    if not www_dir.exists():
        try:
            www_dir.mkdir(parents=True, exist_ok=True)
            context.io.log(f"Created {www_dir}")
        except PermissionError:
            context.io.warning(f"Could not create {www_dir} — run as root if needed")

    return True
