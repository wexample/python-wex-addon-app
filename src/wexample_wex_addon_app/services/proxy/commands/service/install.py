from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_wex_core.const.globals import COMMAND_TYPE_SERVICE

from wexample_wex_addon_app.const.tags import DomainTag

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.service.app_service import AppService

_SERVICE_DIR = Path(__file__).resolve().parents[2]
_PROXY_SAMPLES_SRC = _SERVICE_DIR / "samples" / "proxy"


@command(
    type=COMMAND_TYPE_SERVICE,
    description="Install proxy service files into the target app",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.NETWORK,
        DomainTag.PROXY,
        DomainTag.SERVICE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def proxy__service__install(
    context: ExecutionContext,
    service: AppService,
) -> None:
    app_workdir = service.app_workdir
    app_path = app_workdir.get_path()

    proxy_target_dir = app_path / "proxy"
    proxy_target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_PROXY_SAMPLES_SRC, proxy_target_dir, dirs_exist_ok=True)

    config_file = app_workdir.get_config_file()
    config = config_file.read_config()
    config.set_by_path("port.public", 80)
    config.set_by_path("port.public_secure", 443)
    config_file.write_config(config)
    app_workdir.get_runtime_config(rebuild=True)

    context.io.log(f"Installed proxy samples into {app_path}")
