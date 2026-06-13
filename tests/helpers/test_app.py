from __future__ import annotations

import platform
import socket
from pathlib import Path

import pytest


def test_get_sidecar_path_builds_var_www_path() -> None:
    from wexample_wex_addon_app.helpers.app import get_sidecar_path

    assert get_sidecar_path("worker", "prod") == Path("/var/www/prod/wex-worker")


def test_get_docker_local_ip_returns_loopback_on_darwin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wexample_wex_addon_app.helpers.app import get_docker_local_ip

    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    assert get_docker_local_ip() == "127.0.0.1"


def test_get_docker_local_ip_falls_back_when_hostname_lookup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    from wexample_wex_addon_app.helpers import app as app_module
    from wexample_wex_addon_app.helpers.app import get_docker_local_ip

    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(shutil, "which", lambda _: None)

    def _raise(_: str) -> str:
        raise OSError("boom")

    monkeypatch.setattr(socket, "gethostbyname", _raise)

    assert get_docker_local_ip() == app_module._DEFAULT_LOCAL_IP
