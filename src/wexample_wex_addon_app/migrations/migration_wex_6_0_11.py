from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6011(AbstractMigration):
    VERSION = "6.0.11"
    DESCRIPTION = "Normalize domain config: domain_main/domain_tld → domain, clean up domains list"

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        if not wex_dir.is_dir():
            return

        config_files = [wex_dir / "config.yml"]
        env_dir = wex_dir / "env"
        if env_dir.is_dir():
            for env_path in env_dir.iterdir():
                if env_path.is_dir():
                    config_files.append(env_path / "config.yml")

        for config_path in config_files:
            if not config_path.exists():
                continue

            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            if not isinstance(config, dict):
                continue

            changed = False

            # domain_main or domain_tld → domain (domain_main takes priority)
            for old_key in ("domain_main", "domain_tld"):
                if old_key in config and "domain" not in config:
                    config["domain"] = config.pop(old_key)
                    changed = True
                elif old_key in config:
                    config.pop(old_key)
                    changed = True

            # domains: keep only if it has extras beyond domain
            domain = config.get("domain")
            domains = config.get("domains")
            if isinstance(domains, list):
                extras = [d for d in domains if d and d != domain]
                if not extras:
                    # Only contained the main domain — redundant, clear it
                    config.pop("domains", None)
                    changed = True
                elif domain and domain not in domains:
                    # Main domain missing from extras list — add it
                    config["domains"] = [domain] + extras
                    changed = True

            if changed:
                with open(config_path, "w") as f:
                    yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)
