from __future__ import annotations

import os
from typing import TYPE_CHECKING

from wexample_helpers.classes.private_field import private_field
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers.helpers.module import module_load_class_from_file
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_prompt.common.progress.progress_handle import ProgressHandle
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


@base_class
class AppAddonManager(AbstractAddonManager):
    _app_workdir: ProjectWorkdir | None = private_field(
        default=None, description="The current managed app workdir"
    )

    def app_workdir(
        self, reload: bool = False
    ) -> ProjectWorkdir | None:
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

        if reload:
            self._app_workdir = None

        if self._app_workdir is not None:
            return self._app_workdir

        app_path = self.kernel.call_workdir.get_path()
        custom_app_workdir_class_path = self.kernel.workdir.get_path() / "app_workdir.py"
        if custom_app_workdir_class_path.exists():
            app_workdir_class = module_load_class_from_file(
                file_path=custom_app_workdir_class_path,
                class_name="AppWorkdir"
            )
        else:
            app_workdir_class = ProjectWorkdir

        # Use basic project class to access minimal configuration.
        self._app_workdir = app_workdir_class.create_from_path(
            path=app_path,
            parent_io_handler=self.kernel,
        )

        return self._app_workdir
