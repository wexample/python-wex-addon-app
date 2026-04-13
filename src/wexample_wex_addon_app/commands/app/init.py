from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
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
@command(type=COMMAND_TYPE_ADDON, description="Initialize an app")
def app__app__init(
    context: ExecutionContext,
    name: str | None = None,
    services: list[str] | None = None,
    env: str | None = None,
    app_path: str | None = None,
) -> None:
    from wexample_helpers.helpers.string import string_to_snake_case

    from wexample_wex_addon_app.commands.file_state.rectify import app__file_state__rectify
    from wexample_wex_addon_app.commands.service.install import app__service__install

    target_path = Path(app_path or context.kernel.call_workdir.get_path()).resolve()
    app_name = name or target_path.name
    env_name = env or "local"
    normalized_services = [string_to_snake_case(s) for s in (services or [])]

    for subdir in [".wex", ".wex/tmp"]:
        (target_path / subdir).mkdir(parents=True, exist_ok=True)

    (target_path / ".wex" / "config.yml").write_text(
        "global:\n"
        f"  name: {app_name}\n"
        "  version: 1.0.0\n"
        "  type: app\n"
    )
    (target_path / ".wex" / ".env").write_text(f"APP_ENV={env_name}\n")

    for service_name in normalized_services:
        context.kernel.run_function(
            app__service__install,
            {"app_path": str(target_path), "service": service_name},
        )

    context.kernel.run_function(
        app__file_state__rectify,
        {"app_path": str(target_path), "yes": True},
    )

    context.io.log(f"Initialized app '{app_name}' at {target_path}")
