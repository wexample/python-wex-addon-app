from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def test_install_dependencies_calls_per_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers import python as python_module

    calls: list[tuple] = []
    monkeypatch.setattr(
        python_module,
        "python_install_dependency_in_venv",
        lambda venv_path, name, editable: calls.append((name, editable)),
    )

    python_module.python_install_dependencies_in_venv(
        tmp_path, ["a", "b"], editable=True
    )

    assert calls == [("a", True), ("b", True)]


def test_is_package_installed_editable_false_when_not_editable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers.python import (
        python_is_package_installed_editable_in_venv,
    )

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _Result(0, "Name: pkg\nVersion: 1.0\n")
    )

    assert (
        python_is_package_installed_editable_in_venv(tmp_path, "pkg", tmp_path) is False
    )


def test_is_package_installed_editable_false_when_paths_differ(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers.python import (
        python_is_package_installed_editable_in_venv,
    )

    other = tmp_path / "other"
    stdout = f"Editable project location: {other}\n"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(0, stdout))

    assert (
        python_is_package_installed_editable_in_venv(tmp_path, "pkg", tmp_path) is False
    )


def test_is_package_installed_editable_false_when_pip_show_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers.python import (
        python_is_package_installed_editable_in_venv,
    )

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(1))

    assert (
        python_is_package_installed_editable_in_venv(tmp_path, "pkg", tmp_path) is False
    )


def test_is_package_installed_editable_false_when_subprocess_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers.python import (
        python_is_package_installed_editable_in_venv,
    )

    def _raise(*a, **k) -> None:
        raise OSError("no python")

    monkeypatch.setattr(subprocess, "run", _raise)

    assert (
        python_is_package_installed_editable_in_venv(tmp_path, "pkg", tmp_path) is False
    )


def test_is_package_installed_editable_true_when_paths_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wexample_wex_addon_app.helpers.python import (
        python_is_package_installed_editable_in_venv,
    )

    stdout = f"Name: pkg\nEditable project location: {tmp_path}\n"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(0, stdout))

    assert (
        python_is_package_installed_editable_in_venv(tmp_path, "pkg", tmp_path) is True
    )


class _Result:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
