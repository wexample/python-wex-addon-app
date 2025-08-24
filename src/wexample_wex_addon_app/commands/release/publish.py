from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(description="Publish the Python package to PyPI.")
def app__release__publish(
    context: ExecutionContext,
) -> None:
    _python_app__release__publish(context=context)


# TODO Find a way to define that current app is a python package (services ?)
def _python_app__release__publish(
    context: ExecutionContext,
) -> None:
    from wexample_helpers.helpers.shell import shell_run

    workdir = context.request.get_addon_manager().app_workdir

    # Map token to PyPI's token-based authentication if provided
    username = "__token__"
    password = workdir.get_env_parameter("PIPY_TOKEN")

    # Build the publish command, adding credentials only when given
    publish_cmd = ["pdm", "publish"]
    if username is not None:
        publish_cmd += ["--username", username]
    if password is not None:
        publish_cmd += ["--password", password]

    shell_run(
        publish_cmd,
        inherit_stdio=True,
    )
