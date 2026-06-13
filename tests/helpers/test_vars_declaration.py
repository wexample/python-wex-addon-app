from __future__ import annotations

from typing import Any


def test_gen_hex_returns_64_hex_chars() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _gen_hex

    value = _gen_hex()

    assert len(value) == 64
    assert all(c in "0123456789abcdef" for c in value)


def test_generators_registry_has_known_kinds() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _GENERATORS

    assert set(_GENERATORS) == {"token", "hex", "urlsafe"}
    assert all(callable(g) for g in _GENERATORS.values())


def test_is_present_false_when_absent_everywhere() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _is_present

    assert _is_present(_Workdir(), "FOO", {}, {}) is False


def test_is_present_handles_build_runtime_failure() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _is_present

    class _W:
        def build_runtime_config_value(self) -> None:
            raise RuntimeError("boom")

    assert _is_present(_W(), "FOO", {}, {}) is False


def test_is_present_true_via_build_runtime_config() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _is_present

    class _W:
        def build_runtime_config_value(self) -> _Runtime:
            return _Runtime({"FOO": "x"})

    assert _is_present(_W(), "FOO", {}, {}) is True


def test_is_present_true_via_suite_fallback() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _is_present

    class _W:
        def get_env_parameter_or_suite_fallback(self, key: str, default=None) -> str:
            return "found"

    assert _is_present(_W(), "FOO", {"use_suite_fallback": True}, {}) is True


def test_is_present_true_when_in_existing_env() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import _is_present

    assert _is_present(_Workdir(), "FOO", {}, {"FOO": "x"}) is True


def test_process_vars_declarations_generates_missing_token() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    workdir = _Workdir()
    process_vars_declarations(
        {"SECRET": {"generated": "hex"}}, app_workdir=workdir, io=_Io("")
    )

    assert "SECRET" in workdir.env
    assert len(workdir.env["SECRET"]) == 64


def test_process_vars_declarations_noop_when_empty() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    workdir = _Workdir()
    process_vars_declarations({}, app_workdir=workdir, io=_Io(""))

    assert workdir.set_calls == []


def test_process_vars_declarations_prompts_for_required() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    workdir = _Workdir()
    io = _Io("entered-value")
    process_vars_declarations(
        {"API_KEY": {"required": True, "description": "the key"}},
        app_workdir=workdir,
        io=io,
    )

    assert workdir.env["API_KEY"] == "entered-value"
    assert io.inputs[0][0] == "API_KEY — the key"


def test_process_vars_declarations_skips_default_when_already_set() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    workdir = _Workdir(env={"PORT": "9000"})
    process_vars_declarations(
        {"PORT": {"default": 8080}}, app_workdir=workdir, io=_Io("")
    )

    assert workdir.set_calls == []
    assert workdir.env["PORT"] == "9000"


def test_process_vars_declarations_writes_silent_default() -> None:
    from wexample_wex_addon_app.helpers.vars_declaration import (
        process_vars_declarations,
    )

    workdir = _Workdir()
    process_vars_declarations(
        {"PORT": {"default": 8080}}, app_workdir=workdir, io=_Io("")
    )

    assert workdir.env["PORT"] == "8080"


class _Params:
    def __init__(self, data: dict) -> None:
        self._data = data

    def to_dict(self) -> dict:
        return dict(self._data)


class _Runtime:
    def __init__(self, data: dict) -> None:
        self._data = data

    def to_dict(self) -> dict:
        return dict(self._data)


class _Workdir:
    def __init__(self, env: dict | None = None) -> None:
        self.env: dict = dict(env or {})
        self.set_calls: list[dict] = []

    def get_env_parameters(self) -> _Params:
        return _Params(self.env)

    def set_env_parameters(self, values: dict) -> None:
        self.set_calls.append(dict(values))
        self.env.update(values)


class _Resp:
    def __init__(self, value: Any) -> None:
        self._value = value

    def get_value(self) -> Any:
        return self._value


class _Io:
    def __init__(self, value: Any) -> None:
        self._value = value
        self.inputs: list[tuple] = []

    def input(self, question: str, default_value: Any = None) -> _Resp:
        self.inputs.append((question, default_value))
        return _Resp(self._value)

    def log(self, message: str) -> None:
        pass
