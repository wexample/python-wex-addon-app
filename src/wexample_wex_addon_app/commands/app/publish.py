from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.response.queued_collection_response import QueuedCollectionResponse
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.code_base_middleware import CodeBaseMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir


@option(
    name="yes",
    type=bool,
    default=False,
    is_flag=True,
    description="Non-interactive mode",
)
@option(
    name="no_bump",
    type=bool,
    default=False,
    is_flag=True,
    description="Skip version bump",
)
@option(
    name="skip_rectify",
    type=bool,
    default=False,
    is_flag=True,
    description="Skip file state rectification",
)
@option(
    name="force",
    type=bool,
    default=False,
    is_flag=True,
    description="Force bump even if no changes detected",
)
@middleware(middleware=CodeBaseMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish a new version of the app: bump, rectify, commit, tag.",
)
def app__app__publish(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
    yes: bool = False,
    no_bump: bool = False,
    skip_rectify: bool = False,
    force: bool = False,
) -> QueuedCollectionResponse:
    def _bump(previous_value=None) -> QueuedCollectionStopResponse:
        from wexample_app.response.queue_collection.queued_collection_stop_response import (
            QueuedCollectionStopResponse,
        )

        bumped = app_workdir.bump(interactive=not yes, force=force)
        if not bumped:
            return QueuedCollectionStopResponse(
                kernel=context.kernel,
                reason="Bump aborted — publication cancelled.",
            )

    def _rectify(previous_value=None) -> None:
        from wexample_wex_addon_app.commands.state.rectify import (
            app__state__rectify,
        )

        context.kernel.run_function(
            app__state__rectify,
            arguments={"loop": True, "yes": yes},
        )

    def _commit(previous_value=None) -> None:
        app_workdir.commit_changes()
        app_workdir.push_to_deployment_remote()
        context.io.success(f"Pushed {app_workdir.get_project_name()}.")

    def _tag(previous_value=None) -> None:
        app_workdir.add_publication_tag()
        context.io.success(
            f"Published {app_workdir.get_project_name()} v{app_workdir.get_project_version()}."
        )

    steps = []
    if not no_bump:
        steps.append(_bump)
    if not skip_rectify:
        steps.append(_rectify)
    steps.append(_commit)
    steps.append(_tag)

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
