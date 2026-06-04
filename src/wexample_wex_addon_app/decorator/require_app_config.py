from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wexample_cli.common.command_method_wrapper import CommandMethodWrapper
    from wexample_helpers.const.types import AnyCallable

_SENTINEL = object()


def check_config_requirements(
    requirements: list[dict],
    app_workdir: Any,
    io: Any,
    function_kwargs: dict,
) -> None:
    for req in requirements:
        _check_one(req, app_workdir, io, function_kwargs)


def require_app_config(
    path: str,
    type: type | None = None,
    default: Any = _SENTINEL,
    values: list | Callable | None = None,
    description: str | None = None,
    ask_question: str | None = None,
    on_missing: str = "error",
    values_empty_hint: str | None = None,
) -> AnyCallable:
    """Declare a required (or defaulted) app config key, checked before command execution.

    - on_missing="error" (default): raises ValueError with a clear message
    - on_missing="ask": prompts the user (choice if values provided, else free input) and persists
    - default=X: uses X silently and persists it to config.yml
    - values_empty_hint: extra message appended when ``values`` resolves to an empty list
      (e.g. "Run 'wex app/config-build' first to generate the compose file.").
    """

    def decorator(command_wrapper: CommandMethodWrapper) -> CommandMethodWrapper:
        from wexample_cli.common.command_method_wrapper import CommandMethodWrapper

        if not isinstance(command_wrapper, CommandMethodWrapper):
            raise TypeError(
                f"@require_app_config must decorate a CommandMethodWrapper "
                "(apply @command before @require_app_config)."
            )

        if "config_requirements" not in command_wrapper.extra:
            command_wrapper.extra["config_requirements"] = []
        command_wrapper.extra["config_requirements"].append(
            {
                "path": path,
                "type": type,
                "default": default,
                "values": values,
                "description": description,
                "ask_question": ask_question,
                "on_missing": on_missing,
                "values_empty_hint": values_empty_hint,
            }
        )
        return command_wrapper

    return decorator


def _check_one(req: dict, app_workdir: Any, io: Any, function_kwargs: dict) -> None:
    from wexample_wex_addon_app.exception.config_requirement_exception import (
        ConfigRequirementException,
    )

    path = req["path"]
    type_ = req["type"]
    default = req["default"]
    values = req["values"]
    description = req["description"]
    ask_question = req["ask_question"]
    on_missing = req["on_missing"]
    values_empty_hint = req.get("values_empty_hint")

    config_value = app_workdir.get_runtime_config().search(path)

    if not config_value.is_none():
        value = _read_typed(config_value, type_)
        if values is not None:
            allowed = _resolve_values(values, function_kwargs)
            if not allowed:
                raise ConfigRequirementException(
                    message=_empty_values_message(path, values_empty_hint),
                    path=path,
                    value=str(value),
                    allowed=[],
                )
            if value not in allowed:
                raise ConfigRequirementException(
                    message=(
                        f"Config @cyan{{{path}}} = {value!r} is not in allowed "
                        f"values: {allowed}"
                    ),
                    path=path,
                    value=str(value),
                    allowed=list(allowed),
                )
        return

    if default is not _SENTINEL:
        app_workdir.write_config_value(path, default)
        return

    if on_missing == "ask":
        question = ask_question or (
            f"Config @cyan{{{path}}} is not set"
            + (f" — {description}" if description else "")
            + ":"
        )

        if values is not None:
            allowed = _resolve_values(values, function_kwargs)
            if not allowed:
                raise ConfigRequirementException(
                    message=_empty_values_message(path, values_empty_hint),
                    path=path,
                    allowed=[],
                )
            value = io.choice(question=question, choices=allowed).get_answer()
        else:
            value = io.input(question=question).get_value()

        if value is not None:
            app_workdir.write_config_value(path, value)
        return

    raise ConfigRequirementException(
        message=(
            f"Required config @cyan{{{path}}}"
            + (f" ({description})" if description else "")
            + " is missing from .wex/config.yml"
        ),
        path=path,
    )


def _empty_values_message(path: str, hint: str | None) -> str:
    base = f"Config @cyan{{{path}}}: no valid value available (allowed values list is empty)."
    return f"{base} {hint}" if hint else base


def _read_typed(config_value: Any, target_type: type | None) -> Any:
    if target_type is int:
        return config_value.get_int()
    if target_type is bool:
        return config_value.get_bool()
    return config_value.get_str()


def _resolve_values(values: list | Callable, kwargs: dict[str, Any]) -> list:
    if not callable(values):
        return values
    sig = inspect.signature(values)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return values(**filtered)
