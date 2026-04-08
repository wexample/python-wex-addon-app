from __future__ import annotations

import os
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.helpers.app import get_docker_local_ip

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import ManagedWorkdir

_HOSTS_PATH = "/etc/hosts"
_WEX_BLOCK_START = "#[ wex ]#"
_WEX_BLOCK_END = "#[ end-wex ]#"


def _remove_wex_block(content: str) -> str:
    lines = content.split(os.linesep)
    result = []
    in_block = False
    for line in lines:
        if _WEX_BLOCK_START in line:
            in_block = True
        elif _WEX_BLOCK_END in line:
            in_block = False
            continue
        if not in_block:
            result.append(line)
    return os.linesep.join(result)


def _add_wex_block(content: str, block_lines: list[str]) -> str:
    block = os.linesep.join(block_lines)
    return content + f"{_WEX_BLOCK_START}{os.linesep}{block}{os.linesep}{_WEX_BLOCK_END}{os.linesep}"


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Update /etc/hosts with app domains")
def app__hosts__update(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.response.null_response import NullResponse

    runtime = app_workdir.get_runtime_config()
    domains_config = runtime.search("app.domains")

    if domains_config.is_none():
        return NullResponse(kernel=context.kernel)

    domains = [d.get_str() for d in domains_config.get_list_or_default([]) if not d.is_none()]
    if not domains:
        return NullResponse(kernel=context.kernel)

    env = app_workdir.get_app_env()
    ip = (
        get_docker_local_ip()
        if env == "local"
        else runtime.search("app.host.ip").get_str_or_default(get_docker_local_ip())
    )

    with open(_HOSTS_PATH, "r") as f:
        content = f.read()

    content = _remove_wex_block(content)

    # Preserve existing non-current-app entries from the old block (not needed yet, single-app mode)
    new_lines = [f"{ip}\t{domain}" for domain in domains]

    content = _add_wex_block(content, new_lines)

    with open(_HOSTS_PATH, "w") as f:
        f.write(content)

    context.io.log(f"Hosts updated: {', '.join(domains)} → {ip}")

    return NullResponse(kernel=context.kernel)
