from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware


@base_class
class AppMiddleware(AbstractMiddleware):
    pass
