from __future__ import annotations

import fcntl
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import (
    CORE_COMMAND_NAME,
    CORE_FILE_NAME_APPS_REGISTRY,
)

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

_REGISTRY_PATH = Path("/var/lib") / CORE_COMMAND_NAME / CORE_FILE_NAME_APPS_REGISTRY
_REGISTRY_LOCK_PATH = _REGISTRY_PATH.with_suffix(".lock")


def registry_get_path() -> Path:
    return _REGISTRY_PATH


def registry_purge_stopped() -> None:
    """Remove entries whose containers are no longer running."""
    import subprocess

    with _registry_lock():
        data = registry_read()
        active = {}

        for app_path, entry in data["apps"].items():
            tmp_dir = Path(app_path) / ".wex" / "tmp"
            runtime_compose = tmp_dir / "docker-compose.runtime.yml"
            docker_env = tmp_dir / "docker.env"
            if not runtime_compose.exists():
                continue

            cmd = ["docker", "compose"]
            if docker_env.exists():
                cmd += ["--env-file", str(docker_env)]
            cmd += ["-f", str(runtime_compose), "ps", "-q"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                active[app_path] = entry

        data["apps"] = active
        registry_write(data)


def registry_read() -> dict:
    import json

    if not _REGISTRY_PATH.exists():
        return {"apps": {}}

    with open(_REGISTRY_PATH) as f:
        return json.load(f) or {"apps": {}}


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

    with _registry_lock():
        data = registry_read()
        data["apps"][str(app_workdir.get_path())] = {
            "domains": domains,
            "ip": ip,
            "env": env,
        }
        registry_write(data)


def registry_unregister_app(app_workdir: ManagedWorkdir) -> None:
    with _registry_lock():
        data = registry_read()
        data["apps"].pop(str(app_workdir.get_path()), None)
        registry_write(data)


def registry_write(data: dict) -> None:
    import json

    _REGISTRY_PATH.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    with open(_REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)
    _REGISTRY_PATH.chmod(0o644)


@contextmanager
def _registry_lock() -> Generator[None]:
    _REGISTRY_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REGISTRY_LOCK_PATH, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield
        # OS releases the lock automatically when the fd closes
