from __future__ import annotations

from typing import Any

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware


@base_class
class AppMiddleware(AbstractMiddleware):
    def __init__(self, **kwargs) -> None:
        # Define the app_path option
        if "options" not in kwargs:
            kwargs["options"] = []
        
        kwargs["options"].append(self._get_default_option())
        
        super().__init__(**kwargs)
    
    def _get_default_option(self) -> dict[str, Any]:
        """Get the default app_path option definition."""
        return {
            "name": "app_path",
            "type": str,
            "required": False,
            "description": "Path to the app directory (defaults to current directory)",
        }
