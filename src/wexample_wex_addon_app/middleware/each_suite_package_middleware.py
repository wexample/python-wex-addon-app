from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware


@base_class
class EachSuitePackageMiddleware(AppMiddleware):
    pass
