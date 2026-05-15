from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wexample_helpers.const.types import AnyCallable
    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper


def check_env_requirements(
    requirements: list[dict],
    app_workdir: Any,
    io: Any,
    function_kwargs: dict,
) -> None:
    for req in requirements:
        _check_one(req, app_workdir, io, function_kwargs)


def require_local_env(
    key: str | Callable,
    description: str | None = None,
    ask_question: str | None = None,
    on_missing: str = "ask",
    use_suite_fallback: bool = False,
) -> AnyCallable:
    """Declare an env var required by this command. Check happens before execution.

    - key: str (static) or Callable(**function_kwargs) -> str | None (dynamic).
      Returning None from the callable means "not required in this context"
      (e.g. a token only needed for some publication strategies).
    - on_missing="ask" (default): prompt the user and persist to .wex/local/env.yml.
    - on_missing="error": raise with a wex command suggestion to fix.
    - use_suite_fallback=True: if the workdir is part of a package suite,
      look up the var on the suite parent when missing locally
      (requires `get_env_parameter_or_suite_fallback` on the workdir).
    """

    def decorator(command_wrapper: CommandMethodWrapper) -> CommandMethodWrapper:
        from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper

        if not isinstance(command_wrapper, CommandMethodWrapper):
            raise TypeError(
                "@require_local_env must decorate a CommandMethodWrapper "
                "(apply @command before @require_local_env)."
            )

        if "env_requirements" not in command_wrapper.extra:
            command_wrapper.extra["env_requirements"] = []
        command_wrapper.extra["env_requirements"].append(
            {
                "key": key,
                "description": description,
                "ask_question": ask_question,
                "on_missing": on_missing,
                "use_suite_fallback": use_suite_fallback,
            }
        )
        return command_wrapper

    return decorator


def _check_one(req: dict, app_workdir: Any, io: Any, function_kwargs: dict) -> None:
    key = _resolve_key(req["key"], app_workdir, function_kwargs)
    if key is None:
        return  # callable signalled "not required in this context"

    description = req["description"]
    ask_question = req["ask_question"]
    on_missing = req["on_missing"]
    use_suite_fallback = req.get("use_suite_fallback", False)

    value = _lookup(app_workdir, key, use_suite_fallback)
    if value:
        return

    if on_missing == "ask":
        question = ask_question or (
            f"Env var @cyan{{{key}}} is not set"
            + (f" — {description}" if description else "")
            + ":"
        )
        response = io.input(question=question)
        new_value = response.get_value()
        if new_value:
            app_workdir.set_env_parameters({key: new_value})
        return

    from wexample_wex_core.resolver.addon_command_resolver import AddonCommandResolver

    from wexample_wex_addon_app.commands.env.var_set import app__env__var_set

    suggestion = AddonCommandResolver.build_command_from_function(
        app__env__var_set, {"key": key, "value": "<value>"}
    )
    io.suggestions(
        message=(
            f"Env var @cyan{{{key}}} is required"
            + (f" ({description})" if description else "")
            + " and not set in .wex/local/env.yml."
        ),
        suggestions=[suggestion],
    )
    raise ValueError(f"Missing required env var: {key}")


def _lookup(app_workdir: Any, key: str, use_suite_fallback: bool) -> str | None:
    if use_suite_fallback:
        fallback = getattr(app_workdir, "get_env_parameter_or_suite_fallback", None)
        if fallback is None:
            raise TypeError(
                f"use_suite_fallback=True but {type(app_workdir).__name__} does not "
                "support get_env_parameter_or_suite_fallback()."
            )
        return fallback(key, default=None)
    return app_workdir.get_env_parameter(key, default=None)


def _resolve_key(
    key: str | Callable, app_workdir: Any, function_kwargs: dict[str, Any]
) -> str | None:
    if not callable(key):
        return key
    candidates = dict(function_kwargs)
    candidates.setdefault("app_workdir", app_workdir)
    sig = inspect.signature(key)
    filtered = {k: v for k, v in candidates.items() if k in sig.parameters}
    return key(**filtered)
