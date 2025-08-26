from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(description="Publish the Python package to PyPI.")
def app__release__publish(
    context: ExecutionContext,
) -> None:
    workdir = context.request.get_addon_manager().app_workdir()
    workdir.publish()
