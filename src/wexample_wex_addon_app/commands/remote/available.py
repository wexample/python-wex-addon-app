from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="env",
    short_name="e",
    type=str,
    required=True,
    description="Target environment (must match a .wex/env/<env>/config.yml)",
)
@option(
    name="name",
    type=str,
    required=False,
    default=None,
    description="Remote name (omit to use the first one)",
)
@option(
    name="timeout",
    type=int,
    required=False,
    default=3,
    description="HTTP timeout in seconds",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Check whether the webhook daemon on the selected remote responds on /health"
    ),
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.NETWORK,
        DomainTag.SSH,
        EffectTag.IDEMPOTENT,
        EffectTag.NETWORK_CALL,
        EffectTag.READ_ONLY,
        EffectTag.SUBPROCESS_SPAWN,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
        ScopeTag.REMOTE,
    ],
)
def app__remote__available(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    env: str,
    name: str | None = None,
    timeout: int = 3,
) -> bool:
    from http.client import HTTPConnection

    from wexample_wex_addon_app.helpers.remote import remote_resolve

    try:
        remote = remote_resolve(app_workdir=app_workdir, env=env, name=name)
    except ValueError as e:
        context.io.warning(str(e))
        return False

    host = remote["host"]
    webhook_port = remote["webhook_port"]
    address = f"{host}:{webhook_port}"
    context.io.log(f"Checking webhook on {remote['name']} ({address})")

    try:
        conn = HTTPConnection(host, webhook_port, timeout=timeout)
        conn.request("GET", "/health")
        status = conn.getresponse().status
        ok = status == 200
    except Exception as e:
        context.io.warning(f"Webhook on {address} not reachable: {e}")
        return False

    if ok:
        context.io.success(f"Webhook on {address} is up")
    else:
        context.io.warning(f"Webhook on {address} returned HTTP {status}")

    return ok
