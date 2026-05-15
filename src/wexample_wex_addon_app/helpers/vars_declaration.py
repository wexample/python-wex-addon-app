"""Common processing of a `vars:` declaration block.

Used by both:
  - `service.yml → vars:` (consumed by `app::service/install`)
  - `config.yml → vars:` (consumed at `app::start` and other commands)

The declaration format is identical between the two contexts:

    vars:
      MY_VAR:
        required: true              # if True, prompt the user when missing
        default: "fallback"         # written silently when present and not required
        description: "..."          # shown in the prompt
        generated: "token"          # auto-generate value (token|hex|urlsafe), persist in env.yml
        use_suite_fallback: false   # accept value found at the suite parent

Resolution order, for each var that is not already set:
  1. `generated:` (auto-gen + persist, no prompt)
  2. `required: true` (prompt user + persist)
  3. `default:` without `required` (write silently)
  4. Otherwise: skip
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from wexample_prompt.common.io_manager import IoManager


def _gen_token() -> str:
    from wexample_helpers.helpers.string import string_random_token

    return string_random_token()


def _gen_hex() -> str:
    import secrets

    return secrets.token_hex(32)


def _gen_urlsafe() -> str:
    import secrets

    return secrets.token_urlsafe(24)


_GENERATORS: dict[str, Callable[[], str]] = {
    "token": _gen_token,
    "hex": _gen_hex,
    "urlsafe": _gen_urlsafe,
}


def process_vars_declarations(
    vars_decl: dict[str, dict],
    app_workdir: Any,
    io: IoManager,
) -> None:
    """Apply a vars: declaration block: generate, default, prompt, persist.

    All persistence goes through `app_workdir.set_env_parameters()` which writes
    to `.wex/local/env.yml` and updates env_config in memory.
    """
    if not vars_decl:
        return

    existing_env = app_workdir.get_env_parameters().to_dict()

    # Step 1: auto-generated values (token/hex/urlsafe) for missing vars
    to_generate: dict[str, str] = {}
    for key, meta in vars_decl.items():
        gen = meta.get("generated")
        if not gen or gen is True:
            continue  # legacy `generated: true` = skip (set elsewhere by code)
        if gen not in _GENERATORS:
            continue
        if _is_present(app_workdir, key, meta, existing_env):
            continue
        to_generate[key] = _GENERATORS[gen]()
    if to_generate:
        app_workdir.set_env_parameters(to_generate)
        existing_env = app_workdir.get_env_parameters().to_dict()

    # Step 2: silent defaults (non-required, has default, not yet set)
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

    # Step 3: prompt the user for required vars
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
