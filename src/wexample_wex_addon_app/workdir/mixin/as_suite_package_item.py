from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers.helpers.directory import directory_iterate_parent_dirs

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@base_class
class AsSuitePackageItem(BaseClass):
    def find_suite_workdir_path(self) -> Path:
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        def _found(path: Path) -> bool:
            config = AppWorkdirMixin.get_config_from_path(
                path=path,
            )
            if config:
                if config.read_config().search('app.is_suite').is_true():
                    return True

            return False

        directory_iterate_parent_dirs(
            path=self.get_path(),
            condition=_found
        )

        return self.find_closest(FrameworkPackageSuiteWorkdir)
