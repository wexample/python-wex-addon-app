from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from wexample_helpers.const.types import StringKeysDict

if TYPE_CHECKING:
    from wexample_helpers.const.types import StringKeysDict


class AppConfig(TypedDict):
    branch: str | None
    domain_main: str
    domain_tld: str
    domains: list[str]
    domains_string: str
    env: StringKeysDict
    host: dict[str, str]
    name: str
    password: dict[str, str]
    path: dict[str, str]
    server: StringKeysDict
    service: StringKeysDict
    started: bool
    user: dict[str, str | int]
