from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext

_CONFIG_KEY = "git"
_STRATEGY_KEY = "publication_strategy"
_DEFAULT_VALUE = "main_push"


class Migration_6_0_25__1(AbstractMigration):
    VERSION = "6.0.25"
    SEQ = 1
    DESCRIPTION = (
        "Add git.publication_strategy: main_push to .wex/config.yml if not already set."
    )

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        if not isinstance(config, dict):
            return

        git_section = config.get(_CONFIG_KEY)
        if isinstance(git_section, dict) and _STRATEGY_KEY in git_section:
            return

        if not context.dry_run:
            if not isinstance(git_section, dict):
                git_section = {}
            git_section[_STRATEGY_KEY] = _DEFAULT_VALUE
            config[_CONFIG_KEY] = git_section

            with open(config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)

    def rollback(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.exists():
            return

        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        if not isinstance(config, dict):
            return

        git_section = config.get(_CONFIG_KEY)
        if not isinstance(git_section, dict):
            return

        if git_section.get(_STRATEGY_KEY) != _DEFAULT_VALUE:
            return

        if not context.dry_run:
            del git_section[_STRATEGY_KEY]
            if not git_section:
                del config[_CONFIG_KEY]
            with open(config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)
