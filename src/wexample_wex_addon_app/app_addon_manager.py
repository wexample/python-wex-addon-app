from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_app.const.globals import APP_PATH_APP_MANAGER
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_helpers.const.types import PathOrString
    from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware

    from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir


@base_class
class AppAddonManager(AbstractAddonManager):
    @classmethod
    def get_package_module(cls) -> Any:
        import wexample_wex_addon_app

        return wexample_wex_addon_app

    @classmethod
    def get_shell_manager_path(cls) -> Path:
        from wexample_app.const.globals import APP_FILE_APP_MANAGER

        return (
            cls.get_package_source_path() / "resources" / f"{APP_FILE_APP_MANAGER}.sh"
        )

    def create_app_workdir(
        self, path: PathOrString | None = None
    ) -> BasicAppWorkdir | None:
        from pathlib import Path

        from wexample_helpers.helpers.cli import cli_make_clickable_path
        from wexample_helpers.helpers.module import module_load_class_from_file

        from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

        app_path = (
            Path(path) if path is not None else self.kernel.call_workdir.get_path()
        )

        if not BasicAppWorkdir.is_app_workdir_path(path=app_path):
            self.kernel.warning(
                f"Path does not match with an application directory structure: {cli_make_clickable_path(app_path)}"
            )
            return None

        custom_app_workdir_class_path = (
            app_path / APP_PATH_APP_MANAGER / "app_workdir.py"
        )
        if custom_app_workdir_class_path.exists():
            app_workdir_class = module_load_class_from_file(
                file_path=custom_app_workdir_class_path, class_name="AppWorkdir"
            )
        else:
            app_workdir_class = BasicAppWorkdir

        # Use basic project class to access minimal configuration.
        return app_workdir_class.create_from_path(
            path=app_path.resolve(),
            parent_io_handler=self.kernel,
        )

    def get_middlewares_classes(self) -> list[type[AbstractMiddleware]]:
        from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
        from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
            EachSuitePackageMiddleware,
        )
        from wexample_wex_addon_app.middleware.package_suite_middleware import (
            PackageSuiteMiddleware,
        )
        from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import (
            SuiteOrEachPackageMiddleware,
        )

        return [
            AppMiddleware,
            EachSuitePackageMiddleware,
            PackageSuiteMiddleware,
            SuiteOrEachPackageMiddleware,
        ]
