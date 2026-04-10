from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

_REGISTRY_PATH = Path.home() / ".local" / "share" / "cli" / "registry.yml"


def registry_get_path() -> Path:
    return _REGISTRY_PATH


def registry_read() -> dict:
    from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read

    if not _REGISTRY_PATH.exists():
        return {"apps": {}}

    return yaml_read(file_path=str(_REGISTRY_PATH), default={"apps": {}}) or {"apps": {}}


def registry_write(data: dict) -> None:
    import yaml

    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REGISTRY_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def registry_register_app(app_workdir: ManagedWorkdir) -> None:
    runtime = app_workdir.get_runtime_config()
    domains_config = runtime.search("app.domains")
    domains = (
        [d.get_str() for d in domains_config.get_list_or_default([]) if not d.is_none()]
        if not domains_config.is_none()
        else []
    )
    ip = runtime.search("app.host.ip").get_str_or_default("127.0.1.1")
    env = app_workdir.get_app_env()

    data = registry_read()
    data["apps"][str(app_workdir.get_path())] = {
        "domains": domains,
        "ip": ip,
        "env": env,
    }
    registry_write(data)


def registry_unregister_app(app_workdir: ManagedWorkdir) -> None:
    data = registry_read()
    data["apps"].pop(str(app_workdir.get_path()), None)
    registry_write(data)


def registry_purge_stopped() -> None:
    """Remove entries whose containers are no longer running."""
    import subprocess

    data = registry_read()
    active = {}

    for app_path, entry in data["apps"].items():
        runtime_compose = Path(app_path) / ".wex" / "tmp" / "docker-compose.runtime.yml"
        if not runtime_compose.exists():
            continue

        result = subprocess.run(
            ["docker", "compose", "-f", str(runtime_compose), "ps", "-q"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            active[app_path] = entry

    data["apps"] = active
    registry_write(data)
