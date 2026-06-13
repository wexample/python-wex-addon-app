from __future__ import annotations

from typing import Any

import pytest


def test_remote_resolve_raises_when_host_missing() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    workdir = _Workdir([{"name": "a", "host": "   "}])

    with pytest.raises(ValueError, match="no 'host' field"):
        remote_resolve(workdir, env="prod")


def test_remote_resolve_raises_when_named_remote_missing() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    workdir = _Workdir([{"name": "a", "host": "h"}])

    with pytest.raises(ValueError, match="Remote 'b' not found"):
        remote_resolve(workdir, env="prod", name="b")


def test_remote_resolve_raises_when_no_remotes() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    with pytest.raises(ValueError, match="No remotes defined"):
        remote_resolve(_Workdir(None), env="prod")


def test_remote_resolve_raises_when_user_unresolvable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    monkeypatch.delenv("USER", raising=False)
    workdir = _Workdir([{"name": "a", "host": "h"}])

    with pytest.raises(ValueError, match="Could not resolve SSH user"):
        remote_resolve(workdir, env="prod")


def test_remote_resolve_returns_full_descriptor() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    workdir = _Workdir(
        [{"name": "main", "host": "example.com", "user": "deploy"}], project="myapp"
    )

    resolved = remote_resolve(workdir, env="prod")

    assert resolved == {
        "name": "main",
        "host": "example.com",
        "user": "deploy",
        "webhook_port": 7654,
        "path": "/var/www/prod/myapp",
        "env": "prod",
    }


def test_remote_resolve_selects_named_remote() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    workdir = _Workdir(
        [
            {"name": "a", "host": "a.com", "user": "u"},
            {"name": "b", "host": "b.com", "user": "u", "webhook_port": 9000},
        ]
    )

    resolved = remote_resolve(workdir, env="prod", name="b")

    assert resolved["host"] == "b.com"
    assert resolved["webhook_port"] == 9000


def test_remote_resolve_user_override_takes_precedence() -> None:
    from wexample_wex_addon_app.helpers.remote import remote_resolve

    workdir = _Workdir([{"name": "a", "host": "h", "user": "configured"}])

    resolved = remote_resolve(workdir, env="prod", user_override="override")

    assert resolved["user"] == "override"


class _Search:
    def __init__(self, value: Any) -> None:
        self._value = value

    def to_list_or_none(self) -> Any:
        return self._value


class _Config:
    def __init__(self, remotes: Any) -> None:
        self._remotes = remotes

    def search(self, _key: str) -> _Search:
        return _Search(self._remotes)


class _Workdir:
    def __init__(self, remotes: Any, project: str = "proj") -> None:
        self._remotes = remotes
        self._project = project

    def get_config(self, env_name: str) -> _Config:
        return _Config(self._remotes)

    def get_project_name(self) -> str:
        return self._project
