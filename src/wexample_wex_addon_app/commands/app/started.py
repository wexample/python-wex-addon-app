from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.boolean_response import BooleanResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir

APP_STARTED_CHECK_MODE_CONFIG = "config"
APP_STARTED_CHECK_MODE_FULL = "full"
APP_STARTED_CHECK_MODE_ANY_CONTAINER = "any-container"


@option(
    name="mode",
    type=str,
    required=False,
    default=APP_STARTED_CHECK_MODE_ANY_CONTAINER,
    description="How to determine if app is started: config | any-container | full",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Return true if app is started")
def app__app__started(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    mode: str = APP_STARTED_CHECK_MODE_ANY_CONTAINER,
) -> BooleanResponse:
    from wexample_app.response.boolean_response import BooleanResponse

    return BooleanResponse(
        kernel=context.kernel,
        content=_check_started(app_workdir, mode, context),
    )


def _check_started(app_workdir: ManagedWorkdir, mode: str, context) -> bool:
    import subprocess

    import yaml
    from wexample_app.const.globals import WORKDIR_SETUP_DIR

    wex_path = app_workdir.get_path() / WORKDIR_SETUP_DIR

    # Read Docker runtime state
    runtime_path = wex_path / "tmp" / "config.runtime.yml"
    if not runtime_path.exists():
        context.io.log("Runtime config file is missing")
        return False

    with open(runtime_path) as f:
        runtime = yaml.safe_load(f) or {}

    if not runtime.get("started", False):
        context.io.log("Runtime config is marked as stopped")
        return False

    if mode == APP_STARTED_CHECK_MODE_CONFIG:
        return True

    # Get container names from docker-compose.runtime.yml
    compose_path = wex_path / "tmp" / "docker-compose.runtime.yml"
    if not compose_path.exists():
        context.io.log("Runtime docker-compose file is missing")
        return False

    with open(compose_path) as f:
        compose = yaml.safe_load(f) or {}

    container_names = [
        attrs.get("container_name", service)
        for service, attrs in compose.get("services", {}).items()
    ]

    # Check running containers
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    running = (
        set(result.stdout.strip().splitlines()) if result.stdout.strip() else set()
    )

    all_runs = True
    for name in container_names:
        if name in running:
            context.io.log(f"Container {name} runs")
            if mode == APP_STARTED_CHECK_MODE_ANY_CONTAINER:
                return True
        else:
            all_runs = False
            context.io.log(f"Container {name} does not run")
            if mode == APP_STARTED_CHECK_MODE_FULL:
                return False

    return all_runs
