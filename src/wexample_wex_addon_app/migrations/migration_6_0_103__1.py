from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


def _extract_server_ip(server) -> str | None:
    if isinstance(server, str):
        return server.strip() or None
    if isinstance(server, dict):
        value = server.get("ip") or server.get("host")
        return value.strip() if isinstance(value, str) and value.strip() else None
    return None


def _dedup_server_into_remotes(config: dict) -> bool:
    """Move `server.ip` into `remotes[0].host` and drop `server:`. Handles the
    case where an empty `remotes:` skeleton was created by `config/suggest`
    before migration 6.0.90 had a chance to fill it (so 6.0.90 bailed out and
    left `server:` + empty `remotes:` side-by-side).

    Returns True if the config was modified.
    """
    if not isinstance(config, dict):
        return False

    if "server" not in config:
        return False

    server_ip = _extract_server_ip(config["server"])

    remotes = config.get("remotes")
    if isinstance(remotes, list) and remotes:
        # remotes already exists. Fill empty host from server.ip if we can.
        first = remotes[0] if isinstance(remotes[0], dict) else None
        if first is None:
            return False
        current_host = first.get("host")
        if not (isinstance(current_host, str) and current_host.strip()):
            if not server_ip:
                return False
            first["host"] = server_ip
        # In all cases where `server` co-exists with a usable `remotes`, drop it.
        del config["server"]
        return True

    # No remotes yet. This is the same case migration 6.0.90 handles, but we
    # cover it again here in case anyone hand-edited a `server:` back in.
    if not server_ip:
        return False
    config["remotes"] = [{"name": "main", "host": server_ip}]
    del config["server"]
    return True


class Migration_6_0_103__1(AbstractMigration):
    VERSION = "6.0.103"
    SEQ = 1
    DESCRIPTION = (
        "Deduplicate `server:` and `remotes:` in env configs. When both are "
        "present (because `config/suggest` created an empty `remotes:` "
        "skeleton before migration 6.0.90 could promote `server:`), fill the "
        "empty `remotes[0].host` from `server.ip` and drop `server:` so "
        "`remotes[].host` is the only source of truth."
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

            if not _dedup_server_into_remotes(config):
                continue

            migrated.append(env_config_path)

            if context.dry_run:
                continue

            with open(env_config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)

        kernel = context.extras.get("kernel")
        if kernel and migrated:
            kernel.io.log(
                f"Deduplicated `server:` → `remotes:` in {len(migrated)} env config(s)."
            )

    def rollback(self, context: MigrationContext) -> None:
        # No reliable rollback: we can't tell whether the original config had
        # both keys or only `remotes`. Leaving rollback as a no-op is safer
        # than re-introducing `server:` blindly.
        return
