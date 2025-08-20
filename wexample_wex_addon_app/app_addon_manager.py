from functools import cached_property
from typing import TYPE_CHECKING

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class AppAddonManager(AbstractAddonManager):
    @cached_property
    def app_workdir(self) -> "ProjectWorkdir":
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

        path = self.kernel.call_workdir.get_path()
        workdir = ProjectWorkdir.create_from_path(
            path=path,
            io=self.kernel.io,
        )

        from wexample_wex_addon_app.const.globals import APP_FILE_APP_CONFIG
        config_yml = workdir.find_by_name_recursive(APP_FILE_APP_CONFIG)
        if config_yml is not None:
            manager_config = config_yml.read_as_config().search('files_state.manager')
            file_relative = manager_config.get_config_item('file')
            class_name = manager_config.get_config_item('class')
