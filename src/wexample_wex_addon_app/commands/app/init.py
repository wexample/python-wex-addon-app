from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(
    name="name",
    short_name="n",
    type=str,
    required=False,
    description="App name (defaults to current directory name)",
)
@option(
    name="services",
    short_name="s",
    type=str,
    required=False,
    multiple=True,
    always_list=True,
    description="Service names to install",
)
@option(
    name="env",
    short_name="e",
    type=str,
    required=False,
    description="App environment",
)
@option(
    name="app_path",
    short_name="a",
    type=str,
    required=False,
    description="Target app path (defaults to current directory)",
)
# as_sudo is required upfront: service installs triggered by --services may run rectify
# operations that need elevated permissions (e.g. chown on data directories).
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Initialize an app")
def app__app__init(
    context: ExecutionContext,
    name: str | None = None,
    services: list[str] | None = None,
    env: str | None = None,
    app_path: str | None = None,
) -> None:
    import yaml
    from wexample_app.const.globals import (
        APP_DIR_DOCKER,
        APP_FILE_APP_CONFIG,
        APP_PATH_DOCKER_COMPOSE,
        APP_PATH_LOCAL_ENV,
        APP_PATH_TMP,
        CORE_COMMAND_NAME,
        WORKDIR_SETUP_DIR,
    )
    from wexample_helpers.helpers.file import (
        file_mkdir_as_real_user,
        file_write_as_real_user,
    )
    from wexample_helpers.helpers.string import (
        string_to_kebab_case,
        string_to_snake_case,
    )

    from wexample_wex_addon_app.commands.service.install import app__service__install
    from wexample_wex_addon_app.commands.state.rectify import (
        app__state__rectify,
    )

    target_path = Path(app_path or context.kernel.call_workdir.get_path()).resolve()
    app_name = name or target_path.name
    env_name = env or "local"
    normalized_services = [string_to_snake_case(s) for s in (services or [])]
    domain = f"{string_to_kebab_case(app_name)}.{CORE_COMMAND_NAME}"
    wex_version = context.kernel.workdir.get_setup_version()

    for subdir in [
        WORKDIR_SETUP_DIR,
        APP_PATH_TMP,
        APP_DIR_DOCKER,
        APP_PATH_LOCAL_ENV.parent,
    ]:
        file_mkdir_as_real_user(target_path / subdir)

    docker_compose_path = target_path / APP_PATH_DOCKER_COMPOSE
    if not docker_compose_path.exists():
        file_write_as_real_user(docker_compose_path, "services: {}\n")

    file_write_as_real_user(
        target_path / WORKDIR_SETUP_DIR / APP_FILE_APP_CONFIG,
        "global:\n"
        f"  name: {app_name}\n"
        "  version: 1.0.0\n"
        "  type: app\n"
        f"domain: {domain}\n"
        "wex:\n"
        f"  version: {wex_version}\n",
    )
    file_write_as_real_user(
        target_path / APP_PATH_LOCAL_ENV,
        yaml.safe_dump({"APP_ENV": env_name}, sort_keys=False),
    )

    for service_name in normalized_services:
        context.kernel.run_function(
            app__service__install,
            {"app_path": str(target_path), "service": service_name},
        )

    context.kernel.run_function(
        app__state__rectify,
        {"app_path": str(target_path), "yes": True, "loop": True},
    )

    context.io.log(f"Initialized app '{app_name}' at {target_path}")
