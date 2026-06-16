from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_3__1(AbstractMigration):
    VERSION = "6.0.3"
    SEQ = 1
    DESCRIPTION = (
        "Move env-specific config files from .wex/<service>/<name>.<env>.<ext> "
        "to .wex/env/<env>/<service>/<name>.<ext>"
    )
    ENVIRONMENTS = frozenset(("prod", "dev", "local", "test"))
    SERVICE_WHITELIST = (
        "apache",
        "cron",
        "docker",
        "gitlab",
        "hubot",
        "maria",
        "mongo",
        "mysql",
        "n8n",
        "php",
        "postgres",
        "redis",
        "sonarqube",
        "sqlserver",
        "tmp",
        "uploads",
    )

    @classmethod
    def _parse_env_file(cls, filename: str) -> tuple[str, str] | None:
        parts = filename.split(".")
        if len(parts) < 3:
            return None

        env_name = parts[-2]
        if env_name not in cls.ENVIRONMENTS:
            return None

        generic_name = ".".join(parts[:-2]) + "." + parts[-1]
        return generic_name, env_name

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        for service_name in self.SERVICE_WHITELIST:
            service_dir = wex_dir / service_name
            if not service_dir.is_dir():
                continue

            for source in service_dir.iterdir():
                if not source.is_file():
                    continue

                parsed = self._parse_env_file(source.name)
                if parsed is None:
                    continue

                generic_name, env_name = parsed
                generic_path = service_dir / generic_name
                env_dir = wex_dir / "env" / env_name / service_name
                env_dir.mkdir(parents=True, exist_ok=True)

                target_path = env_dir / generic_name
                if not generic_path.exists():
                    shutil.copy2(source, generic_path)

                if target_path.exists() or target_path.is_symlink():
                    target_path.unlink()

                source.rename(target_path)
