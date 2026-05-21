from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_6__1(AbstractMigration):
    VERSION = "6.0.6"
    SEQ = 1
    DESCRIPTION = (
        "Move per-environment config from .wex/config.yml env.* to "
        ".wex/env/<env>/config.yml"
    )

    @classmethod
    def _merge_with_existing_priority(
        cls,
        source: dict[str, Any],
        existing: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(source)

        for key, existing_value in existing.items():
            source_value = merged.get(key)
            if isinstance(source_value, dict) and isinstance(existing_value, dict):
                merged[key] = cls._merge_with_existing_priority(
                    source=source_value,
                    existing=existing_value,
                )
            else:
                merged[key] = existing_value

        return merged

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        root_config_path = wex_dir / "config.yml"
        if not root_config_path.exists():
            return

        with open(root_config_path) as file:
            root_config = yaml.safe_load(file) or {}

        if not isinstance(root_config, dict):
            return

        env_config = root_config.get("env")
        if not isinstance(env_config, dict):
            return

        treated_envs: list[str] = []
        for env_name, env_values in env_config.items():
            if not isinstance(env_values, dict):
                continue

            env_config_path = wex_dir / "env" / str(env_name) / "config.yml"
            env_config_path.parent.mkdir(parents=True, exist_ok=True)

            if env_config_path.exists():
                with open(env_config_path) as file:
                    existing_config = yaml.safe_load(file) or {}
            else:
                existing_config = {}

            if not isinstance(existing_config, dict):
                existing_config = {}

            merged_config = self._merge_with_existing_priority(
                source=env_values,
                existing=existing_config,
            )

            with open(env_config_path, "w") as file:
                yaml.safe_dump(merged_config, file, sort_keys=False)

            treated_envs.append(str(env_name))
            logging.warning("Migration 6.0.6 treated env '%s'", env_name)

        if not treated_envs:
            return

        root_config.pop("env", None)
        with open(root_config_path, "w") as file:
            yaml.safe_dump(root_config, file, sort_keys=False)
