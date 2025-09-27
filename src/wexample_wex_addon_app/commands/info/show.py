from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

from wexample_wex_core.decorator.command import command


@command()
def app__info__show(
        context: ExecutionContext,
) -> None:
    context.io.log('App info')
