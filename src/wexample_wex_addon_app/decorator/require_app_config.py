from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from wexample_helpers.const.types import AnyCallable
    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper

_SENTINEL = object()


def require_app_config(
    path: str,
    type: type | None = None,
    default: Any = _SENTINEL,
    values: list | Callable | None = None,
    description: str | None = None,
    ask_question: str | None = None,
    on_missing: str = "error",
) -> AnyCallable:
    """Declare a required (or defaulted) app config key, checked before command execution.

    - on_missing="error" (default): raises ValueError with a clear message
    - on_missing="ask": prompts the user (choice if values provided, else free input) and persists
    - default=X: uses X silently and persists it to config.yml

    The `values` callable receives the same kwargs as the command function (filtered by name).
    """
    def decorator(command_wrapper: CommandMethodWrapper) -> CommandMethodWrapper:
        from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper

        if not isinstance(command_wrapper, CommandMethodWrapper):
            raise TypeError(
                f"@require_app_config must decorate a CommandMethodWrapper "
                "(apply @command before @require_app_config)."
            )

        original_function = command_wrapper.function

        def wrapped(**kwargs):
            app_workdir = kwargs.get("app_workdir")
            context = kwargs.get("context")
            io = context.io

            config_value = app_workdir.get_runtime_config().search(path)

            if not config_value.is_none():
                value = _read_typed(config_value, type)
                if values is not None:
                    allowed = _resolve_values(values, kwargs)
                    if value not in allowed:
                        raise ValueError(
                            f"Config {path!r} = {value!r} is not in allowed values: {allowed}"
                        )
                return original_function(**kwargs)

            # Config is missing — apply resolution strategy
            if default is not _SENTINEL:
                app_workdir.write_config_value(path, default)
                return original_function(**kwargs)

            if on_missing == "ask":
                question = ask_question or (
                    f"Config @cyan{{{path}}} is not set"
                    + (f" — {description}" if description else "")
                    + ":"
                )
                allowed = _resolve_values(values, kwargs) if values is not None else None

                if allowed:
                    value = io.choice(question=question, choices=allowed).get_answer()
                else:
                    value = io.input(question=question).get_value()

                if value is not None:
                    app_workdir.write_config_value(path, value)
                return original_function(**kwargs)

            # on_missing="error"
            raise ValueError(
                f"Required config @cyan{{{path}}}"
                + (f" ({description})" if description else "")
                + " is missing from .wex/config.yml"
            )

        command_wrapper.function = wrapped
        return command_wrapper

    return decorator


def _resolve_values(values: list | Callable, kwargs: dict[str, Any]) -> list:
    if not callable(values):
        return values
    sig = inspect.signature(values)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return values(**filtered)


def _read_typed(config_value: Any, target_type: type | None) -> Any:
    if target_type is int:
        return config_value.get_int()
    if target_type is bool:
        return config_value.get_bool()
    return config_value.get_str()
