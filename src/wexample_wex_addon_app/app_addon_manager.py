from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr
from wexample_prompt.common.progress.progress_handle import ProgressHandle
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class AppAddonManager(AbstractAddonManager):
    _app_workdir: ProjectWorkdir | None = PrivateAttr(default=None)

    def app_workdir(
        self, reload: bool = False, progress: ProgressHandle | None = None
    ) -> ProjectWorkdir | None:
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

        if reload:
            self._app_workdir = None

        if self._app_workdir is not None:
            return self._app_workdir

        progress = self.kernel.io.progress_handle_create_or_update(
            progress=progress, label="Initializing app workdir...", total=2, current=0
        )

        path = self.kernel.call_workdir.get_path()
        # Use basic project class to access minimal configuration.
        self._app_workdir = ProjectWorkdir.create_from_path(
            path=path,
            io=self.kernel.io,
        )

        preferred = self._app_workdir.get_preferred_workdir_class()
        if preferred:
            progress.advance(step=1)

            self._app_workdir = preferred.create_from_path(
                path=path,
                io=self.kernel.io,
            )

        progress.finish()

        return self._app_workdir
