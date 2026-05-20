from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_filestate.enum.scopes import Scope


def build_scopes(filter_scope: str | None) -> set[Scope]:
    from wexample_filestate.enum.scopes import Scope

    all_scopes = set(Scope)

    if not filter_scope:
        return all_scopes

    result = set(all_scopes)
    for part in filter_scope.split(","):
        part = part.strip()
        if part.startswith("!"):
            name = part[1:].upper()
            result -= {s for s in all_scopes if s.name == name}
        else:
            result &= {s for s in all_scopes if s.name == part.upper()}

    return result
