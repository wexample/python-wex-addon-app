from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


WEBHOOK_PORT_DEFAULT = 7654


def remote_resolve(
    app_workdir: ManagedWorkdir,
    env: str,
    name: str | None = None,
    user_override: str | None = None,
) -> ResolvedRemote:
    remotes_raw = (
        app_workdir.get_config(env_name=env).search("remotes").to_list_or_none()
    )

    if not remotes_raw:
        raise ValueError(
            f"No remotes defined for env '{env}' in .wex/env/{env}/config.yml "
            f"(if this env isn't deployed anywhere, that's expected — "
            f"otherwise add a `remotes:` block with `host:` filled)"
        )

    remotes = [r if isinstance(r, dict) else {} for r in remotes_raw]

    if name is not None:
        matches = [r for r in remotes if r.get("name") == name]
        if not matches:
            available = ", ".join(str(r.get("name", "?")) for r in remotes)
            raise ValueError(
                f"Remote '{name}' not found for env '{env}' (available: {available})"
            )
        selected = matches[0]
    else:
        selected = remotes[0]

    host = selected.get("host")
    if not isinstance(host, str) or not host.strip():
        raise ValueError(
            f"Remote '{selected.get('name', '?')}' (env {env}) has no 'host' field — "
            f"fill it in .wex/env/{env}/config.yml under `remotes[].host`, or "
            f"drop the `remotes:` block entirely if this env isn't deployed"
        )
    host = host.strip()

    resolved_user = (
        user_override or selected.get("user") or os.environ.get("USER") or ""
    )
    if not resolved_user:
        raise ValueError(
            "Could not resolve SSH user (no --user, no remote.user, no $USER)"
        )

    return {
        "name": str(selected.get("name", "main")),
        "host": str(host),
        "user": str(resolved_user),
        "webhook_port": int(selected.get("webhook_port", WEBHOOK_PORT_DEFAULT)),
        "path": f"/var/www/{env}/{app_workdir.get_project_name()}",
        "env": env,
    }


class ResolvedRemote(TypedDict):
    env: str
    host: str
    name: str
    path: str
    user: str
    webhook_port: int
