from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

_ALLOWED_ROLLBACK_KEYS: frozenset[str] = frozenset({"name", "host"})

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


def _migrate_env_config(config: dict) -> bool:
    """Transform legacy `server:` (scalar IP or `{ip: ...}` dict) into
    `remotes: [{name: main, host: <ip>}]`. Returns True if the config was
    modified."""
    if not isinstance(config, dict):
        return False

    if "remotes" in config:
        return False

    if "server" not in config:
        return False

    server = config["server"]

    if isinstance(server, str):
        host = server.strip()
    elif isinstance(server, dict):
        host = server.get("ip") or server.get("host")
        if not isinstance(host, str):
            return False
        host = host.strip()
    else:
        return False

    if not host:
        return False

    del config["server"]
    config["remotes"] = [{"name": "main", "host": host}]
    return True


def _rollback_env_config(config: dict) -> bool:
    if not isinstance(config, dict):
        return False

    remotes = config.get("remotes")
    if not isinstance(remotes, list) or len(remotes) != 1:
        return False

    only = remotes[0]
    if not isinstance(only, dict):
        return False
    if any(k not in _ALLOWED_ROLLBACK_KEYS for k in only):
        return False
    if only.get("name") != "main":
        return False

    host = only.get("host")
    if not isinstance(host, str):
        return False

    del config["remotes"]
    config["server"] = host
    return True


class Migration_6_0_90__1(AbstractMigration):
    VERSION = "6.0.90"
    SEQ = 1
    DESCRIPTION = (
        "Convert legacy `server:` env config (scalar IP or {ip: ...}) into "
        "`remotes: [{name: main, host: <ip>}]`. Required by remote_resolve() "
        "which now expects the multi-remote schema."
    )

    def apply(self, context: MigrationContext) -> None:
        env_dir = context.target_path / ".wex" / "env"
        if not env_dir.is_dir():
            return

        migrated: list[Path] = []

        for env_subdir in sorted(env_dir.iterdir()):
            if not env_subdir.is_dir():
                continue
            env_config_path = env_subdir / "config.yml"
            if not env_config_path.is_file():
                continue

            try:
                with open(env_config_path) as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                continue

            if not _migrate_env_config(config):
                continue

            migrated.append(env_config_path)

            if context.dry_run:
                continue

            with open(env_config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)

        kernel = context.extras.get("kernel")
        if kernel and migrated:
            kernel.io.log(
                f"Converted `server:` → `remotes:` in {len(migrated)} env config(s)."
            )

    def rollback(self, context: MigrationContext) -> None:
        env_dir = context.target_path / ".wex" / "env"
        if not env_dir.is_dir():
            return

        for env_subdir in sorted(env_dir.iterdir()):
            if not env_subdir.is_dir():
                continue
            env_config_path = env_subdir / "config.yml"
            if not env_config_path.is_file():
                continue

            try:
                with open(env_config_path) as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                continue

            if not _rollback_env_config(config):
                continue

            if context.dry_run:
                continue

            with open(env_config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)
