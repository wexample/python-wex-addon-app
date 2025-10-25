from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from wexample_helpers.classes.private_field import private_field
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin


@base_class
class AppAddonManager(AbstractAddonManager):
    _app_workdir: AppWorkdirMixin | None = private_field(
        default=None, description="The current managed app workdir"
    )

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

    def app_workdir(self, reload: bool = False) -> AppWorkdirMixin | None:
        from wexample_helpers.helpers.module import module_load_class_from_file
        from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

        if reload:
            self._app_workdir = None

        if self._app_workdir is not None:
            return self._app_workdir

        app_path = self.kernel.call_workdir.get_path()
        custom_app_workdir_class_path = (
            self.kernel.workdir.get_path() / "app_workdir.py"
        )
        if custom_app_workdir_class_path.exists():
            app_workdir_class = module_load_class_from_file(
                file_path=custom_app_workdir_class_path, class_name="AppWorkdir"
            )
        else:
            app_workdir_class = BasicAppWorkdir

        # Use basic project class to access minimal configuration.
        self._app_workdir = app_workdir_class.create_from_path(
            path=app_path,
            parent_io_handler=self.kernel,
        )

        return self._app_workdir
