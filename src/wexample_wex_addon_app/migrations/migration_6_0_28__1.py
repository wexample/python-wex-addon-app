from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_migration.migration_context import MigrationContext


# Patterns: replace ${APP_<NAMESPACE>_X} with ${<NAMESPACE>_X} in compose files.
# These are duplicates of the top-level config.yml namespaces, formerly produced
# by `merged["app"]` carrying a full copy of config.yml.
# Real runtime app vars (APP_ENV, APP_DOMAIN, APP_PATH, ...) are NOT touched.
_YAML_SUFFIXES: frozenset[str] = frozenset({".yml", ".yaml"})

_DEAPP_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\$\{APP_BRANCH(:?[^}]*)\}"), r"${BRANCH\1}"),
    (re.compile(r"\$\{APP_DOCKER_([A-Z_]+)(:?[^}]*)\}"), r"${DOCKER_\1\2}"),
    (re.compile(r"\$\{APP_GLOBAL_([A-Z_]+)(:?[^}]*)\}"), r"${GLOBAL_\1\2}"),
    (re.compile(r"\$\{APP_SERVICE_([A-Z_]+)(:?[^}]*)\}"), r"${SERVICE_\1\2}"),
    (re.compile(r"\$\{APP_WEX_([A-Z_]+)(:?[^}]*)\}"), r"${WEX_\1\2}"),
]


def _rewrite(content: str) -> tuple[str, int]:
    """Apply all de-APP_ patterns. Return (new_content, replacement_count)."""
    new = content
    count = 0
    for pattern, replacement in _DEAPP_PATTERNS:
        new, n = pattern.subn(replacement, new)
        count += n
    return new, count


class Migration_6_0_28__1(AbstractMigration):
    VERSION = "6.0.28"
    SEQ = 1
    DESCRIPTION = (
        "De-APP_-ify duplicated namespace prefixes in compose/env yaml files: "
        "${APP_DOCKER_X} → ${DOCKER_X}, ${APP_GLOBAL_X} → ${GLOBAL_X}, "
        "${APP_SERVICE_X} → ${SERVICE_X}, ${APP_WEX_X} → ${WEX_X}, "
        "${APP_BRANCH} → ${BRANCH}. Real runtime app vars are kept untouched."
    )

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        if not wex_dir.is_dir():
            return

        total_files = 0
        total_replacements = 0

        for yml_path in self._iter_yaml_files(wex_dir):
            try:
                original = yml_path.read_text(encoding="utf-8")
            except Exception:
                continue
            new_content, n = _rewrite(original)
            if n == 0:
                continue
            total_files += 1
            total_replacements += n
            if context.dry_run:
                continue
            yml_path.write_text(new_content, encoding="utf-8")

        # Use kernel.io if available; otherwise stay silent (migration runner
        # already logs the version when applied).
        kernel = context.extras.get("kernel")
        if kernel and total_replacements:
            kernel.io.log(
                f"De-APP_-ified {total_replacements} reference(s) "
                f"in {total_files} file(s)."
            )

    def _iter_yaml_files(self, wex_dir: Path) -> None:
        """Yield all .yml/.yaml files under .wex/docker/ and .wex/env/."""
        for sub in ("docker", "env"):
            base = wex_dir / sub
            if not base.is_dir():
                continue
            for path in base.rglob("*"):
                if path.suffix in _YAML_SUFFIXES:
                    yield path
