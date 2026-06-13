from __future__ import annotations

import pytest


def test_build_scopes_exclusion_removes_named_scope() -> None:
    from wexample_wex_addon_app.helpers.scope import build_scopes

    result = build_scopes("!remote")

    names = {s.name for s in result}
    assert "REMOTE" not in names
    assert "CONTENT" in names


@pytest.mark.xfail(
    reason="Multiple inclusions intersect and yield an empty set; "
    "see roadmap helpers-scope-multiple-includes-return-empty",
    strict=True,
)
def test_build_scopes_multiple_inclusions_selects_each() -> None:
    from wexample_wex_addon_app.helpers.scope import build_scopes

    result = build_scopes("content,location")

    assert {s.name for s in result} == {"CONTENT", "LOCATION"}


def test_build_scopes_returns_all_when_empty_string() -> None:
    from wexample_filestate.enum.scopes import Scope

    from wexample_wex_addon_app.helpers.scope import build_scopes

    assert build_scopes("") == set(Scope)


def test_build_scopes_returns_all_when_no_filter() -> None:
    from wexample_filestate.enum.scopes import Scope

    from wexample_wex_addon_app.helpers.scope import build_scopes

    assert build_scopes(None) == set(Scope)


def test_build_scopes_single_inclusion_selects_only_that_scope() -> None:
    from wexample_wex_addon_app.helpers.scope import build_scopes

    result = build_scopes("content")

    assert {s.name for s in result} == {"CONTENT"}
