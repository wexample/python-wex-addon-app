from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.workdir import Workdir


class AppAddonManager(AbstractAddonManager):
    _app_workdir: "Workdir" = PrivateAttr()

    def get_workdir(self) -> "Workdir":
        if not self._app_workdir:
            from wexample_wex_core.workdir.workdir import Workdir
            self._app_workdir = Workdir(
                io=self.kernel.io,
                path=self.kernel.call_workdir.get_path()
            )

        return self._app_workdir
