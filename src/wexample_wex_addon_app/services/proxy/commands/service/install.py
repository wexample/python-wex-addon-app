from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_wex_core.const.globals import COMMAND_TYPE_SERVICE

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.service.app_service import AppService


@command(
    type=COMMAND_TYPE_SERVICE,
    description="Install proxy service files into the target app",
)
def proxy__service__install(
    context: ExecutionContext,
    service: AppService,
) -> None:
    from pathlib import Path

    service_dir = Path(__file__).resolve().parents[2]
    app_path = service.app_workdir.get_path()

    proxy_target_dir = app_path / "proxy"
    proxy_target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        service_dir / "samples" / "proxy", proxy_target_dir, dirs_exist_ok=True
    )

    config_file = service.app_workdir.get_config_file()
    config = config_file.read_config()
    config.set_by_path("port.public", 80)
    config.set_by_path("port.public_secure", 443)
    config_file.write_config(config)
    service.app_workdir.get_runtime_config(rebuild=True)

    context.io.log(f"Installed proxy samples into {app_path}")
