from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

_HOSTS_PATH = "/etc/hosts"
_BLOCK_START = "#[ wex ]#"
_BLOCK_END = "#[ end-wex ]#"
_LINESEP = "\n"


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Update /etc/hosts with all registered app domains",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DNS,
        DomainTag.NETWORK,
        DomainTag.SYSTEM,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__host__update(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.response.success_response import SuccessResponse

    from wexample_wex_addon_app.common.app_registry import (
        registry_purge_stopped,
        registry_read,
    )

    registry_purge_stopped()
    data = registry_read()

    apps = data["apps"]
    block_lines = [
        f"{entry.get('ip', '127.0.1.1')}\t{domain}"
        for entry in apps.values()
        for domain in entry.get("domains", [])
    ]
    total_domains = len(block_lines)

    with open(_HOSTS_PATH) as f:
        content = f.read()

    content = _remove_block(content)

    if block_lines:
        content = _add_block(content, block_lines)

    with open(_HOSTS_PATH, "w") as f:
        f.write(content)

    return SuccessResponse(
        kernel=context.kernel,
        message=(
            f"Hosts updated: {total_domains} domain(s) "
            f"from {len(apps)} app(s)"
        ),
    )


def _add_block(content: str, block_lines: list[str]) -> str:
    block = _LINESEP.join(block_lines)
    return (
        content
        + f"{_BLOCK_START}{_LINESEP}{block}{_LINESEP}{_BLOCK_END}{_LINESEP}"
    )


def _remove_block(content: str) -> str:
    lines = content.split(_LINESEP)
    result = []
    in_block = False
    for line in lines:
        if _BLOCK_START in line:
            in_block = True
        elif _BLOCK_END in line:
            in_block = False
            continue
        if not in_block:
            result.append(line)
    return _LINESEP.join(result)
