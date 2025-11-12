from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.private_field import private_field
from wexample_helpers.decorator.base_class import base_class

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.common.command_request import CommandRequest


@base_class
class PackageSuiteMiddleware(AppMiddleware):
    _fail_if_not_suite_workdir: bool = private_field(
        default=True, description="The called method works only on package suite"
    )

    def _create_app_workdir(
        self, request: CommandRequest, app_path: str
    ) -> BasicAppWorkdir:
        """Create and validate that the app workdir is a FrameworkPackageSuiteWorkdir."""
        from wexample_wex_addon_app.exception.invalid_workdir_type_exception import (
            InvalidWorkdirTypeException,
        )
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        app_workdir = super()._create_app_workdir(request=request, app_path=app_path)

        # Validate that app_workdir is a FrameworkPackageSuiteWorkdir
        if self._fail_if_not_suite_workdir and not self._is_package_suite_workdir(
            workdir=app_workdir
        ):
            suite_path = app_workdir.find_suite_workdir_path()
            raise InvalidWorkdirTypeException(
                workdir_path=app_workdir.get_path(),
                actual_type=app_workdir.__class__.__name__,
                expected_type=FrameworkPackageSuiteWorkdir.__name__,
                suite_path=suite_path,
            )

        return app_workdir

    def _is_package_suite_workdir(self, workdir: BasicAppWorkdir) -> bool:
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        return isinstance(workdir, FrameworkPackageSuiteWorkdir)
