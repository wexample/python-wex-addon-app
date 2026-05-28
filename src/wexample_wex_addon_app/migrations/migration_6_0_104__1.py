from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


def _is_empty_skeleton(remotes) -> bool:
    """True if `remotes` is the placeholder skeleton (single entry, empty host)
    historically produced by `config/suggest --apply`. The new canonical syntax
    for "no remote" is to omit the `remotes:` key entirely.
    """
    if not isinstance(remotes, list) or len(remotes) != 1:
        return False
    entry = remotes[0]
    if not isinstance(entry, dict):
        return False
    host = entry.get("host")
    if isinstance(host, str) and host.strip():
        return False
    # Other fields (user, webhook_port) shouldn't have been filled if host
    # wasn't — but if they are, we leave the entry alone (probably intentional).
    extras = {k: v for k, v in entry.items() if k not in ("name", "host") and v}
    return not extras


def _drop_empty_skeleton(config: dict) -> bool:
    if not isinstance(config, dict):
        return False
    if "remotes" not in config:
        return False
    if not _is_empty_skeleton(config["remotes"]):
        return False
    del config["remotes"]
    return True


class Migration_6_0_104__1(AbstractMigration):
    VERSION = "6.0.104"
    SEQ = 1
    DESCRIPTION = (
        "Drop empty `remotes:[{name: main, host: ''}]` skeletons from env "
        "configs. New canonical syntax for 'not deployed anywhere' is to "
        "omit the `remotes:` key entirely. Only single-entry skeletons with "
        "an empty host are removed — anything filled or with extra fields is "
        "left intact."
    )

    def apply(self, context: MigrationContext) -> None:
        env_dir = context.target_path / ".wex" / "env"
        if not env_dir.is_dir():
            return

        cleaned: list[Path] = []

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

            if not _drop_empty_skeleton(config):
                continue

            cleaned.append(env_config_path)

            if context.dry_run:
                continue

            with open(env_config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)

        kernel = context.extras.get("kernel")
        if kernel and cleaned:
            kernel.io.log(
                f"Dropped empty `remotes:` skeleton from {len(cleaned)} env config(s)."
            )

    def rollback(self, context: MigrationContext) -> None:
        # No rollback: we can't tell which configs originally had a skeleton
        # vs. simply no `remotes:` key. Re-introducing one blindly would be
        # worse than leaving things alone.
        return
