"""Process `config.yml → vars:` declarations of an app workdir."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wexample_prompt.common.io_manager import IoManager


def check_app_vars_requirements(app_workdir: Any, io: IoManager) -> None:
    """Read `config.yml → vars:` and prompt/persist missing values.

    Vars referenced elsewhere in `config.yml` (e.g. `libraries:`) or in the
    docker-compose must be **explicitly** declared in `vars:` to be checked
    here. No magic scan — the rule is the same as for env in general:
    « on déclare ce dont on a besoin, on ne devine pas ».

    Idempotent: skips vars already present in `.wex/local/env.yml` (or in the
    suite parent when `use_suite_fallback: true`).
    """
    from wexample_wex_addon_app.helper.vars_declaration import (
        process_vars_declarations,
    )

    vars_decl = app_workdir.get_config().search("vars").to_dict_or_none()
    if not vars_decl:
        return

    process_vars_declarations(
        vars_decl=vars_decl,
        app_workdir=app_workdir,
        io=io,
    )
