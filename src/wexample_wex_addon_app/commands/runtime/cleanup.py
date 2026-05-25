from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.command import command

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@command(type=COMMAND_TYPE_ADDON)
def app__runtime__cleanup(context: ExecutionContext) -> None:
    removed_containers, removed_images = context.workdir.runtime_cleanup()

    if removed_containers == 0 and removed_images == 0:
        context.io.success("Nothing to clean up.")
    else:
        context.io.success(
            f"Cleaned up {removed_containers} container(s) and {removed_images} image(s)."
        )
