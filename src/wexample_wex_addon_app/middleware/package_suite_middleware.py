from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.common.command_request import CommandRequest


@base_class
class PackageSuiteMiddleware(AppMiddleware):
    def _create_app_workdir(self, request: CommandRequest, app_path: str):
        """Create and validate that the app workdir is a FrameworkPackageSuiteWorkdir."""
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        app_workdir = super()._create_app_workdir(request=request, app_path=app_path)

        # Validate that app_workdir is a FrameworkPackageSuiteWorkdir
        if not isinstance(app_workdir, FrameworkPackageSuiteWorkdir):
            raise TypeError(
                f"The app_workdir `{app_workdir.get_path()}` is of type {app_workdir.__class__.__name__} "
                f"and not a subclass of {FrameworkPackageSuiteWorkdir.__name__}."
            )

        return app_workdir
