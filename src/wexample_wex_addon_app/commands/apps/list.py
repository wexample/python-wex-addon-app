from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(type=COMMAND_TYPE_ADDON, description="List all running apps with their domains and containers")
def app__apps__list(
    context: ExecutionContext,
) -> None:
    from wexample_wex_addon_app.commands.container.list import app__container__list
    from wexample_wex_addon_app.common.app_registry import registry_read

    data = registry_read()
    apps = data.get("apps", {})

    if not apps:
        context.io.log("No running apps in registry")
        return

    for app_path, entry in apps.items():
        context.io.title(f"{app_path}  [{entry.get('env', '?')}]")

        domains = entry.get("domains") or []
        context.io.log("  Domains: " + (", ".join(domains) if domains else "-"))

        context.io.log("  Containers:")
        context.kernel.run_function(app__container__list, {"app_path": app_path})
