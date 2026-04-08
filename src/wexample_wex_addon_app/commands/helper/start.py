from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="name",
    type=str,
    required=True,
    description="Helper app short name (e.g. proxy)",
)
@option(
    name="env",
    type=str,
    required=False,
    description="Environment (defaults to local)",
)
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Start a helper app")
def app__helper__start(
    context: ExecutionContext,
    name: str,
    env: str | None = None,
) -> AbstractResponse:
    import shutil

    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    env = env or "local"
    helper_path = AppAddonManager.get_helper_app_path(name=name, env=env)

    def _create(previous_value=None) -> None:
        if helper_path.exists():
            from wexample_wex_addon_app.commands.app.started import (
                APP_STARTED_CHECK_MODE_ANY_CONTAINER,
                _check_started,
            )

            helper_workdir = AppAddonManager.from_kernel(context.kernel).create_app_workdir(
                path=helper_path
            )
            if helper_workdir and _check_started(
                helper_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context
            ):
                context.io.log(f"Helper '{name}' already running, skipping creation")
                return

            shutil.rmtree(helper_path)

        # TODO: replace with app__app__init once ported to v6
        # Directory structure
        for subdir in [
            ".wex/docker",
            ".wex/tmp",
            f"{name}/certs",
            f"{name}/html",
            f"{name}/logs",
            f"{name}/vhost.d",
        ]:
            (helper_path / subdir).mkdir(parents=True)

        # .wex/config.yml
        (helper_path / ".wex" / "config.yml").write_text(
            "global:\n"
            f"  type: app\n"
            f"  name: wex-{name}\n"
            f"  main_service: {name}\n"
            "  version: 1.0.0\n"
            "service:\n"
            f"  {name}: {{}}\n"
        )

        # .wex/.env
        (helper_path / ".wex" / ".env").write_text(f"APP_ENV={env}\n")

        # .wex/docker/docker-compose.yml
        from wexample_wex_addon_app.helpers.app import get_helper_docker_compose

        (helper_path / ".wex" / "docker" / "docker-compose.yml").write_text(
            get_helper_docker_compose(name=name)
        )

        # proxy/wex.conf
        from wexample_wex_addon_app.helpers.app import get_helper_wex_conf

        (helper_path / "proxy" / "wex.conf").write_text(get_helper_wex_conf())

        context.io.log(f"Helper '{name}' app created at {helper_path}")

    def _start(previous_value=None):
        from wexample_wex_addon_app.commands.app.start import app__app__start

        return context.kernel.run_function(app__app__start, {"app_path": str(helper_path)})

    return QueuedCollectionResponse(kernel=context.kernel, content=[_create, _start])
