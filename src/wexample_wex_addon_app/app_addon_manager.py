from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class AppAddonManager(AbstractAddonManager):
    @cached_property
    def app_workdir(self) -> ProjectWorkdir:
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

        path = self.kernel.call_workdir.get_path()
        # Use basic project class to access minimal configuration.
        workdir = ProjectWorkdir.create_from_path(
            path=path,
            io=self.kernel.io,
        )

        progress = self.kernel.io.progress(label='Workdir initialization...', total=2).get_handle()

        preferred = workdir.get_preferred_workdir_class()
        if preferred:
            workdir = preferred.create_from_path(
                path=path,
                io=self.kernel.io,
            )

        progress.finish()

        return workdir
