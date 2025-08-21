from typing import Dict, List, Optional, TypedDict

from wexample_helpers.const.types import StringKeysDict


class AppConfig(TypedDict):
    branch: Optional[str]
    domain_main: str
    domain_tld: str
    domains: List[str]
    domains_string: str
    env: StringKeysDict
    name: str
    host: Dict[str, str]
    password: Dict[str, str]
    path: Dict[str, str]
    server: StringKeysDict
    service: StringKeysDict
    started: bool
    user: Dict[str, str | int]
