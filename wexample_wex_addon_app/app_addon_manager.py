from functools import cached_property
from typing import TYPE_CHECKING

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class AppAddonManager(AbstractAddonManager):
    @cached_property
    def app_workdir(self) -> "ProjectWorkdir":
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

        return ProjectWorkdir.create_from_path(
            path=self.kernel.call_workdir.get_path(),
            io=self.kernel.io,
        )
