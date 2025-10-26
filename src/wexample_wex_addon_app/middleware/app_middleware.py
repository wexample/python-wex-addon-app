from __future__ import annotations

from typing import Any

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware


@base_class
class AppMiddleware(AbstractMiddleware):

    def _get_middleware_options(self) -> list[dict[str, Any]]:
        """Get the default file option definition."""
        return [{
            "name": "app_path",
            "type": str,
            "required": False,
            "description": "Path to the app directory (defaults to current directory)",
        }]

