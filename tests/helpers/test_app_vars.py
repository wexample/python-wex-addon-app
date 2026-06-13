from __future__ import annotations

from typing import Any

import pytest


def test_check_app_vars_requirements_delegates_when_vars_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wexample_wex_addon_app.helpers import vars_declaration
    from wexample_wex_addon_app.helpers.app_vars import check_app_vars_requirements

    calls: list[dict] = []
    monkeypatch.setattr(
        vars_declaration,
        "process_vars_declarations",
        lambda **kwargs: calls.append(kwargs),
    )

    workdir = _Workdir({"FOO": {}})
    io = object()
    check_app_vars_requirements(workdir, io=io)

    assert len(calls) == 1
    assert calls[0]["vars_decl"] == {"FOO": {}}
    assert calls[0]["app_workdir"] is workdir
    assert calls[0]["io"] is io


def test_check_app_vars_requirements_noop_when_no_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wexample_wex_addon_app.helpers import vars_declaration
    from wexample_wex_addon_app.helpers.app_vars import check_app_vars_requirements

    calls: list[dict] = []
    monkeypatch.setattr(
        vars_declaration,
        "process_vars_declarations",
        lambda **kwargs: calls.append(kwargs),
    )

    check_app_vars_requirements(_Workdir(None), io=object())

    assert calls == []


class _Search:
    def __init__(self, value: Any) -> None:
        self._value = value

    def to_dict_or_none(self) -> Any:
        return self._value


class _Config:
    def __init__(self, value: Any) -> None:
        self._value = value

    def search(self, _key: str) -> _Search:
        return _Search(self._value)


class _Workdir:
    def __init__(self, value: Any) -> None:
        self._value = value

    def get_config(self) -> _Config:
        return _Config(self._value)
