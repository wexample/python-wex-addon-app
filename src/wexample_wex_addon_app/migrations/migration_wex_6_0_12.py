from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class MigrationWex6012(AbstractMigration):
    VERSION = "6.0.12"
    DESCRIPTION = (
        "Move legacy domain_* entries into canonical domain/domains config "
        "and remove deprecated domain_main/domain_tld keys"
    )

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

            with open(config_path) as file:
                config = yaml.safe_load(file) or {}

            if not isinstance(config, dict):
                continue

            changed = False

            legacy_domain_main = config.pop("domain_main", None)
            legacy_domain_tld = config.pop("domain_tld", None)
            if legacy_domain_main is not None or legacy_domain_tld is not None:
                changed = True

            if "domain" not in config:
                domain = legacy_domain_main or legacy_domain_tld
                if domain:
                    config["domain"] = domain
                    changed = True

            legacy_extra_domains = []
            for key in list(config.keys()):
                if not key.startswith("domain_"):
                    continue

                value = config.pop(key)
                changed = True
                if value:
                    legacy_extra_domains.append(value)

            configured_domains = config.get("domains")
            if isinstance(configured_domains, list) and configured_domains:
                domains = [domain for domain in configured_domains if domain]
            else:
                main_domain = config.get("domain")
                domains = [main_domain] if main_domain else []

            for domain in legacy_extra_domains:
                if domain not in domains:
                    domains.append(domain)

            if domains != config.get("domains"):
                config["domains"] = domains
                changed = True

            if changed:
                with open(config_path, "w") as file:
                    yaml.safe_dump(config, file, sort_keys=False, allow_unicode=True)
