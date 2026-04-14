from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_SERVICE
from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.service.app_service import AppService


@command(
    type=COMMAND_TYPE_SERVICE,
    description="Install proxy service files into the target app",
)
def proxy__service__install(
    context: ExecutionContext,
    service: AppService,
) -> None:
    from wexample_app.const.globals import WORKDIR_SETUP_DIR

    service_dir = Path(__file__).resolve().parents[2]
    app_path = service.app_workdir.get_path()

    proxy_samples_dir = service_dir / "samples" / "proxy"
    compose_sample_path = service_dir / "samples" / "docker" / "docker-compose.yml"

    proxy_target_dir = app_path / "proxy"
    compose_target_path = app_path / WORKDIR_SETUP_DIR / "docker" / "docker-compose.yml"

    proxy_target_dir.parent.mkdir(parents=True, exist_ok=True)
    compose_target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(proxy_samples_dir, proxy_target_dir, dirs_exist_ok=True)
    shutil.copy2(compose_sample_path, compose_target_path)

    config_file = service.app_workdir.get_config_file()
    config = config_file.read_config()
    config.set_by_path("port.public", 80)
    config.set_by_path("port.public_secure", 443)
    config_file.write_config(config)
    service.app_workdir.get_runtime_config(rebuild=True)

    context.io.log(f"Installed proxy samples into {app_path}")
