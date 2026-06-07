from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext


@command(
    type=COMMAND_TYPE_ADDON,
    description="List all running apps with their domains and containers",
    tags=[
        DomainTag.APP_LIFECYCLE,
        EffectTag.READ_ONLY,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__app__list(
    context: ExecutionContext,
) -> AbstractResponse:
    from wexample_app.response.log_response import LogResponse
    from wexample_app.response.multiple_response import MultipleResponse
    from wexample_app.response.title_response import TitleResponse

    from wexample_wex_addon_app.commands.container.list import app__container__list
    from wexample_wex_addon_app.common.app_registry import registry_read

    data = registry_read()
    apps = data.get("apps", {})

    if not apps:
        return LogResponse(
            kernel=context.kernel,
            message="No running apps in registry",
        )

    responses: list[AbstractResponse] = []
    for app_path, entry in apps.items():
        responses.append(
            TitleResponse(
                kernel=context.kernel,
                text=f"{app_path}  [{entry.get('env', '?')}]",
            )
        )

        domains = entry.get("domains") or []
        domains_str = ", ".join(f"@magenta{{{d}}}" for d in domains) if domains else "-"
        responses.append(
            LogResponse(kernel=context.kernel, message=f"  Domains: {domains_str}")
        )

        responses.append(LogResponse(kernel=context.kernel, message="  Containers:"))

        responses.append(
            context.kernel.run_function(app__container__list, {"app_path": app_path})
        )

    return MultipleResponse(kernel=context.kernel, responses=responses)
