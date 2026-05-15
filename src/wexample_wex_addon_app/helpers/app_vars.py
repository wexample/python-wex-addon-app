"""Process `config.yml → vars:` declarations of an app workdir."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wexample_prompt.common.io_manager import IoManager


_VAR_REF_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::-[^}]*)?\}")


def check_app_vars_requirements(app_workdir: Any, io: IoManager) -> None:
    """Read `config.yml → vars:` (+ `libraries:` refs) and prompt/persist missing values.

    Sources merged:
      - `vars:` block — explicit declarations (full schema: required, default,
        description, use_suite_fallback…)
      - `libraries:` block — every `${VAR}` referenced becomes an implicit
        `required: true` declaration (unless already declared explicitly in `vars:`).

    Idempotent: skips vars already present in `.wex/local/env.yml` (or in the
    suite parent when `use_suite_fallback: true`).
    """
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    config = app_workdir.get_config()
    explicit = config.search("vars").to_dict_or_none() or {}
    implicit = _extract_vars_from_libraries(config)

    # Explicit wins over implicit
    merged = {**implicit, **explicit}

    process_vars_declarations(
        vars_decl=merged,
        app_workdir=app_workdir,
        io=io,
    )


def _extract_vars_from_libraries(config: Any) -> dict[str, dict]:
    """Return a vars-style dict for every ${VAR} found in config → libraries:."""
    libraries = config.search("libraries").to_list_or_default() or []
    implicit: dict[str, dict] = {}
    for entry in libraries:
        if not isinstance(entry, str):
            continue
        for match in _VAR_REF_PATTERN.findall(entry):
            implicit.setdefault(
                match,
                {
                    "required": True,
                    "description": "Path referenced in config.yml → libraries:",
                },
            )
    return implicit
