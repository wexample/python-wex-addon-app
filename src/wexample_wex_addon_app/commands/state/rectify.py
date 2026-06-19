from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
    EachSuitePackageMiddleware,
)
from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="dry_run", type=bool, default=False, is_flag=True)
@option(name="loop", type=bool, default=False, is_flag=True)
@option(name="loop_limit", type=int, default=10)
@option(name="filter_scope", type=str, default=None)
@option(name="filter_path", type=str, default=None)
@option(name="filter_operation", type=str, default=None)
@option(name="max", type=int, default=None)
@option(name="force", type=bool, default=False, is_flag=True)
@option(name="changed_only", type=bool, default=False, is_flag=True)
# Rectification may apply chmod/chown on directories owned by other users
# (e.g. www-data in Docker volumes), so elevated permissions are required upfront.
@as_sudo()
@middleware(middleware=AppMiddleware)
@middleware(middleware=EachSuitePackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.CONFIG,
        DomainTag.GIT,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__state__rectify(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    force: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    loop: bool = False,
    loop_limit: int = 10,
    filter_scope: str | None = None,
    filter_path: str | None = None,
    filter_operation: str | None = None,
    max: int = None,
    changed_only: bool = False,
):
    from wexample_app.response.success_response import SuccessResponse
    from wexample_app.response.warning_response import WarningResponse

    from wexample_wex_addon_app.helper.scope import build_scopes

    scopes = build_scopes(filter_scope=filter_scope)

    def compute_filter_paths(cwd) -> list[str] | None:
        paths: list[str] | None = None
        if filter_path:
            paths = [filter_path]
        if changed_only:
            from wexample_helpers_git.helper.git import git_get_changed_paths

            paths = list(git_get_changed_paths(cwd=cwd))
        return paths

    if dry_run:
        workdir = context.request.get_addon_manager().create_app_workdir()
        workdir.dry_run(
            scopes=scopes,
            filter_paths=compute_filter_paths(workdir.get_path()),
            filter_operation=filter_operation,
            max=max,
        )
        return None

    from wexample_filestate.item.abstract_item_target import AbstractItemTarget

    result_response = None
    # Apply changes once, or keep looping until no operations remain (when --loop is set).
    iterations = 0
    while True:
        iterations += 1
        workdir = context.request.get_addon_manager().create_app_workdir()

        result = AbstractItemTarget.apply(
            workdir,
            interactive=(not yes),
            scopes=scopes,
            filter_paths=compute_filter_paths(workdir.get_path()),
            filter_operation=filter_operation,
            max=max,
        )
        n_ops = len(result.operations)

        if n_ops == 0:
            pass_text = "pass" if iterations == 1 else "passes"
            result_response = SuccessResponse(
                kernel=context.kernel,
                message=f"Rectification completed successfully after {iterations} {pass_text}.",
            )
            break

        # Stop immediately after the first pass if looping is disabled.
        if not loop:
            operation_text = "operation" if n_ops == 1 else "operations"
            result_response = (
                f"Rectification pass completed; applied "
                f"{n_ops} {operation_text}."
            )
            break

        if iterations >= loop_limit:
            result_response = WarningResponse(
                kernel=context.kernel,
                message=f"Loop limit reached ({iterations}/{loop_limit}); stopping further passes.",
            )
            break

        context.io.log(
            f"Pass {iterations} completed with {n_ops} operation(s); starting pass {iterations + 1} of {loop_limit}."
        )

    workdir.stop_runners()
    return result_response
