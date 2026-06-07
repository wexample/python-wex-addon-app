from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Validate internal dependencies and propagate versions across all packages in the suite.",
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
def app__version__propagate(
    context: ExecutionContext,
    app_workdir: RepoWorkdir,
) -> None:
    if isinstance(app_workdir, FrameworkPackageSuiteWorkdir):
        context.kernel.log(
            f"Propagating version of suite's packages {app_workdir.get_project_name()}"
        )
        # Propagate versions
        app_workdir.propagate_packages_versions()
    else:
        context.kernel.log(
            f"Propagating version of single package {app_workdir.get_project_name()}"
        )
        # Propagate versions
        app_workdir.propagate_version()
