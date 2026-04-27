from __future__ import annotations

import os
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

_HOSTS_PATH = "/etc/hosts"
_BLOCK_START = "#[ wex ]#"
_BLOCK_END = "#[ end-wex ]#"


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Update /etc/hosts with all registered app domains",
)
def app__host__update(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.response.null_response import NullResponse

    from wexample_wex_addon_app.common.app_registry import (
        registry_purge_stopped,
        registry_read,
    )

    registry_purge_stopped()
    data = registry_read()

    block_lines: list[str] = []
    total_domains = 0
    for entry in data["apps"].values():
        ip = entry.get("ip", "127.0.1.1")
        for domain in entry.get("domains", []):
            block_lines.append(f"{ip}\t{domain}")
            total_domains += 1

    with open(_HOSTS_PATH) as f:
        content = f.read()

    content = _remove_block(content)

    if block_lines:
        content = _add_block(content, block_lines)

    with open(_HOSTS_PATH, "w") as f:
        f.write(content)

    context.io.log(
        f"Hosts updated: {total_domains} domain(s) from {len(data['apps'])} app(s)"
    )

    return NullResponse(kernel=context.kernel)


def _add_block(content: str, block_lines: list[str]) -> str:
    block = os.linesep.join(block_lines)
    return (
        content
        + f"{_BLOCK_START}{os.linesep}{block}{os.linesep}{_BLOCK_END}{os.linesep}"
    )


def _remove_block(content: str) -> str:
    lines = content.split(os.linesep)
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
    return os.linesep.join(result)
