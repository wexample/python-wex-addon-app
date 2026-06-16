from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_filestate.enum.scopes import Scope


def build_scopes(filter_scope: str | None) -> set[Scope]:
    from wexample_filestate.enum.scopes import Scope

    all_scopes = set(Scope)

    if not filter_scope:
        return all_scopes

    name_map = {s.name: s for s in all_scopes}
    result = all_scopes.copy()
    for part in filter_scope.split(","):
        part = part.strip()
        if part.startswith("!"):
            scope = name_map.get(part[1:].upper())
            if scope is not None:
                result.discard(scope)
        else:
            scope = name_map.get(part.upper())
            if scope is not None:
                result &= {scope}
            else:
                result.clear()
                break
        if not result:
            break

    return result
