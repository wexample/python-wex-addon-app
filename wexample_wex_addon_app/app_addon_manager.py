from functools import cached_property
from typing import TYPE_CHECKING

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.workdir import Workdir


class AppAddonManager(AbstractAddonManager):
    @cached_property
    def app_workdir(self) -> "Workdir":
        from wexample_wex_core.workdir.workdir import Workdir
        return Workdir(
            io=self.kernel.io,
            path=self.kernel.call_workdir.get_path()
        )
