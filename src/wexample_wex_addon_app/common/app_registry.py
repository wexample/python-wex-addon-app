from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_filestate.item.file.json_file import JsonFile
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers.service.disk_persisted_registry import DiskPersistedRegistry
from wexample_helpers.service.shared_registry import SharedRegistry
from wexample_helpers.service.with_file_lock_mixin import WithFileLockMixin
from wexample_prompt.common.io_manager import IoManager

from wexample_app.const.globals import WORKDIR_SETUP_DIR
from wexample_app.const.path import APP_DIR_NAME_TMP
from wexample_wex_core.const.globals import (
    CORE_COMMAND_NAME,
    CORE_FILE_NAME_APPS_REGISTRY,
)

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


_REGISTRY_PATH = Path("/var/lib") / CORE_COMMAND_NAME / CORE_FILE_NAME_APPS_REGISTRY


def _build_default_file() -> JsonFile:
    """Build the JsonFile backing the apps registry.

    The registry lives outside any workdir context (system path under /var/lib),
    so we pass a default IoManager and skip option-tree configuration.
    """
    return JsonFile.create_from_path(
        path=_REGISTRY_PATH,
        io=IoManager(),
        configure=False,
    )


@base_class
class AppsRegistry(
    WithFileLockMixin,
    SharedRegistry[dict],
    DiskPersistedRegistry[dict],
):
    """Per-host registry of running apps, persisted to JSON with cross-process locking.

    Combines:
    - DiskPersistedRegistry: load/save JSON.
    - SharedRegistry: globally accessible via AppsRegistry.shared().
    - WithFileLockMixin: atomic read-modify-write across processes.

    Items are flat dicts {"domains": [...], "ip": str, "env": str}, keyed by app path.
    On-disk format wraps items under the "apps" key for stability across versions.
    """

    def __init__(self, container: object | None = None, file: JsonFile | None = None) -> None:
        super().__init__(container=container, file=file or _build_default_file())

    def _get_locked_resource_path(self) -> Path:
        return self._file.get_path()

    def save(self) -> None:
        """Persist items under the `{"apps": ...}` envelope (on-disk format)."""
        payload = {
            "apps": {
                key: (item.serialize() if hasattr(item, "serialize") else item)
                for key, item in self._items.items()
            }
        }
        self._file.write_parsed(payload)

    def load(self, item_class: type | None = None) -> None:
        """Hydrate items from the `{"apps": ...}` envelope."""
        raw = self._file.read_parsed() or {}
        data = raw.get("apps", {})
        self._items.clear()
        for key, entry in data.items():
            if item_class is not None and hasattr(item_class, "hydrate"):
                self._items[key] = item_class.hydrate(entry)
            else:
                self._items[key] = entry

    # ------------------------------------------------------------------
    # Atomic business operations (each one is lock-protected)
    # ------------------------------------------------------------------

    def add_app(self, app_workdir: ManagedWorkdir) -> None:
        runtime = app_workdir.get_runtime_config()
        domains_config = runtime.search("app.domains")
        domains = (
            [
                d.get_str()
                for d in domains_config.get_list_or_default([])
                if not d.is_none()
            ]
            if not domains_config.is_none()
            else []
        )
        ip = runtime.search("app.host.ip").get_str_or_default("127.0.1.1")
        env = app_workdir.get_app_env()

        with self.file_lock():
            self.load()
            self.register(
                {"domains": domains, "ip": ip, "env": env},
                key=str(app_workdir.get_path()),
            )
            self.save()

    def remove_app(self, app_workdir: ManagedWorkdir) -> None:
        with self.file_lock():
            self.load()
            self._items.pop(str(app_workdir.get_path()), None)
            self.save()

    def purge_stopped(self) -> None:
        """Remove entries whose containers are no longer running."""
        import subprocess

        with self.file_lock():
            self.load()
            active: dict[str, dict] = {}

            for app_path, entry in self._items.items():
                tmp_dir = Path(app_path) / WORKDIR_SETUP_DIR / APP_DIR_NAME_TMP
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

            self._items = active
            self.save()


# ----------------------------------------------------------------------
# Public function API — thin wrappers around AppsRegistry.shared()
# ----------------------------------------------------------------------


def registry_get_path() -> Path:
    return _REGISTRY_PATH


def registry_read() -> dict:
    registry = AppsRegistry.shared()
    registry.load()
    return {"apps": dict(registry.get_all())}


def registry_register_app(app_workdir: ManagedWorkdir) -> None:
    AppsRegistry.shared().add_app(app_workdir)


def registry_unregister_app(app_workdir: ManagedWorkdir) -> None:
    AppsRegistry.shared().remove_app(app_workdir)


def registry_purge_stopped() -> None:
    AppsRegistry.shared().purge_stopped()
