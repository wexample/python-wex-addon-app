from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_4__1(AbstractMigration):
    VERSION = "6.0.4"
    SEQ = 1
    DESCRIPTION = (
        "Map v5 docker-compose environment variables to their v6 names in all "
        "docker-compose.yml files under .wex/, excluding tmp/"
    )
    _VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
    _EXACT_MAPPING = {
        "RUNTIME_NAME": "APP_NAME",
        "RUNTIME_ENV": "APP_ENV",
        "RUNTIME_STARTED": "APP_STARTED",
        "RUNTIME_HOST_IP": "APP_HOST_IP",
        "GLOBAL_NAME": "APP_NAME",
        "RUNTIME_GLOBAL_NAME": "APP_NAME",
        "RUNTIME_PATH_APP": "APP_PATH",
        "RUNTIME_PATH_APP_ENV": "APP_SETUP_PATH",
    }

    @classmethod
    def _find_unmapped_v5_variables(cls, content: str) -> list[str]:
        return sorted(
            {
                variable
                for variable in cls._VAR_PATTERN.findall(content)
                if variable.startswith("RUNTIME_") or variable.startswith("GLOBAL_")
            }
        )

    @classmethod
    def _map_variable(cls, variable: str) -> str | None:
        if variable in cls._EXACT_MAPPING:
            return cls._EXACT_MAPPING[variable]

        bind_match = re.fullmatch(r"RUNTIME_BIND_(.+)", variable)
        if bind_match:
            return f"BIND_{bind_match.group(1)}"

        service_compose_match = re.fullmatch(
            r"RUNTIME_SERVICE_([A-Z0-9_]+)_YML_(?:ENV|BASE)",
            variable,
        )
        if service_compose_match:
            return f"SERVICE_{service_compose_match.group(1)}_COMPOSE"

        service_match = re.fullmatch(r"RUNTIME_SERVICE_([A-Z0-9_]+)_(.+)", variable)
        if service_match:
            return f"SERVICE_{service_match.group(1)}_{service_match.group(2)}"

        return None

    @classmethod
    def _replace_known_variables(cls, content: str) -> str:
        def replace(match: re.Match[str]) -> str:
            variable = match.group(1)
            mapped = cls._map_variable(variable)
            return "${" + mapped + "}" if mapped else match.group(0)

        return cls._VAR_PATTERN.sub(replace, content)

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        for compose_path in self._find_compose_files(wex_dir):
            content = compose_path.read_text()
            updated = self._replace_known_variables(content)

            for variable in self._find_unmapped_v5_variables(updated):
                logging.warning(
                    "Unmapped v5 variable left in place in %s: %s",
                    compose_path,
                    variable,
                )

            if updated != content:
                compose_path.write_text(updated)

    def _find_compose_files(self, wex_dir: Path) -> list[Path]:
        return [
            path
            for path in wex_dir.rglob("docker-compose.yml")
            if "tmp" not in path.parts
        ]
