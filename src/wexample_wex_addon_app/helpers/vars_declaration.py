"""Common processing of a `vars:` declaration block.

Used by both:
  - `service.yml → vars:` (consumed by `app::service/install`)
  - `config.yml → vars:` (consumed at `app::start` and other commands)

The declaration format is identical between the two contexts:

    vars:
      MY_VAR:
        required: true        # if True, prompt the user when missing
        default: "fallback"   # written silently when present and not required
        description: "..."    # shown in the prompt
        generated: false      # skip entirely (set by code elsewhere)
        use_suite_fallback: false  # accept value found at the suite parent
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wexample_prompt.common.io_manager import IoManager


def process_vars_declarations(
    vars_decl: dict[str, dict],
    app_workdir: Any,
    io: IoManager,
) -> None:
    """Apply a vars: declaration block: write defaults, prompt required, persist.

    All persistence goes through `app_workdir.set_env_parameters()` which writes
    to `.wex/local/env.yml` and updates env_config in memory.
    """
    if not vars_decl:
        return

    existing_env = app_workdir.get_env_parameters().to_dict()

    defaults_to_write = {
        key: str(meta["default"])
        for key, meta in vars_decl.items()
        if "default" in meta
        and not meta.get("generated")
        and not meta.get("required")
        and not _is_present(app_workdir, key, meta, existing_env)
    }
    if defaults_to_write:
        app_workdir.set_env_parameters(defaults_to_write)
        existing_env = app_workdir.get_env_parameters().to_dict()

    for key, meta in vars_decl.items():
        if meta.get("generated"):
            continue
        if not meta.get("required"):
            continue
        if _is_present(app_workdir, key, meta, existing_env):
            continue

        description = meta.get("description", "")
        question = key + (f" — {description}" if description else "")
        suggested = str(meta["default"]) if "default" in meta else None

        value = None
        while not value:
            if value is not None:
                io.log(f"  '{key}' is required, please enter a value.")
            response = io.input(question=question, default_value=suggested)
            value = response.get_value()

        app_workdir.set_env_parameters({key: value})
        existing_env = app_workdir.get_env_parameters().to_dict()


def _is_present(
    app_workdir: Any, key: str, meta: dict, existing_env: dict
) -> bool:
    """Return True if the var is already set, optionally via suite fallback."""
    if key in existing_env:
        return True
    if meta.get("use_suite_fallback"):
        fallback = getattr(app_workdir, "get_env_parameter_or_suite_fallback", None)
        if fallback is not None and fallback(key, default=None):
            return True
    return False
