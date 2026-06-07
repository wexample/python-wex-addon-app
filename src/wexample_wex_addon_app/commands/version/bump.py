from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@option(
    name="force",
    type=bool,
    default=False,
    is_flag=True,
    description="Force bump even if package has no new content",
)
@option(name="yes", type=bool, default=False, is_flag=True)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Bump version only if package has new content (HEAD not tagged). Use --force to bump regardless of changes.",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.PACKAGE,
        DomainTag.RELEASE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__version__bump(
    context: ExecutionContext,
    app_workdir: RepoWorkdir,
    yes: bool = False,
    force: bool = False,
) -> bool:
    package_name = app_workdir.get_package_name()
    bumped = app_workdir.bump(interactive=not yes, force=force)

    if bumped:
        context.io.success(f"Successfully bumped {package_name}.")
    else:
        context.io.log(f"Bump aborted for {package_name}.")

    return bumped
