from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir


@option(
    name="question",
    type=str,
    required=False,
    description="Question to display to the user",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Prompt user to choose an environment, then persist it via env/set")
def app__env__choose(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    question: str = "Choose an environment",
) -> str | None:
    from wexample_app.const.env import (
        ENV_NAME_DEV,
        ENV_NAME_LOCAL,
        ENV_NAME_PROD,
        ENV_NAME_TEST,
    )

    envs = [ENV_NAME_LOCAL, ENV_NAME_DEV, ENV_NAME_TEST, ENV_NAME_PROD]

    response = context.io.choice(
        question=question,
        choices=envs,
        default=ENV_NAME_LOCAL,
        abort="Abort",
    )

    chosen = response.get_answer()

    if chosen is None:
        context.io.log("Environment selection aborted")
        return None

    app_workdir.set_app_env(chosen)
    context.io.log(f'Environment set to "{chosen}"')

    return chosen
