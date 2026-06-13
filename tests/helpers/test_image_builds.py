from __future__ import annotations

from pathlib import Path

import pytest
from wexample_app.const.globals import APP_FILE_APP_CONFIG, WORKDIR_SETUP_DIR


def test_collect_deps_gathers_transitive_chain() -> None:
    from wexample_wex_addon_app.helpers.image_builds import _collect_deps

    builds = {
        "base": {},
        "mid": {"depends_on": "base"},
        "app": {"depends_on": "mid"},
    }

    assert _collect_deps(builds, "app") == {"app", "mid", "base"}


def test_load_builds_raises_when_config_missing(tmp_path: Path) -> None:
    from wexample_wex_addon_app.helpers.image_builds import load_builds

    with pytest.raises(FileNotFoundError, match="No config.yml"):
        load_builds(tmp_path)


def test_load_builds_raises_when_no_images_section(tmp_path: Path) -> None:
    from wexample_wex_addon_app.helpers.image_builds import load_builds

    _write_config(tmp_path, "docker:\n  other: {}\n")

    with pytest.raises(KeyError, match="No docker.images section"):
        load_builds(tmp_path)


def test_load_builds_returns_images(tmp_path: Path) -> None:
    from wexample_wex_addon_app.helpers.image_builds import load_builds

    _write_config(tmp_path, "docker:\n  images:\n    base: {}\n")

    assert load_builds(tmp_path) == {"base": {}}


def test_resolve_build_order_deps_first_for_all() -> None:
    from wexample_wex_addon_app.helpers.image_builds import resolve_build_order

    builds = {"app": {"depends_on": "base"}, "base": {}}

    order = resolve_build_order(builds)

    assert order.index("base") < order.index("app")
    assert set(order) == {"app", "base"}


def test_resolve_build_order_single_target_includes_transitive_deps() -> None:
    from wexample_wex_addon_app.helpers.image_builds import resolve_build_order

    builds = {
        "base": {},
        "mid": {"depends_on": "base"},
        "app": {"depends_on": "mid"},
        "unrelated": {},
    }

    order = resolve_build_order(builds, name="app")

    assert order == ["base", "mid", "app"]


def test_resolve_build_order_unknown_name_raises() -> None:
    from wexample_wex_addon_app.helpers.image_builds import resolve_build_order

    with pytest.raises(KeyError, match="Build 'ghost' not found"):
        resolve_build_order({"base": {}}, name="ghost")


def _write_config(app_path: Path, body: str) -> None:
    setup_dir = app_path / WORKDIR_SETUP_DIR
    setup_dir.mkdir(parents=True, exist_ok=True)
    (setup_dir / APP_FILE_APP_CONFIG).write_text(body)
