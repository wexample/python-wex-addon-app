from __future__ import annotations

from pathlib import Path

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers.helpers.directory import directory_iterate_parent_dirs


@base_class
class AsSuitePackageItem(BaseClass):
    def find_suite_workdir_path(self) -> Path | None:
        """
        We have to trust the configuration file to know if parent directory is a suite or not,
        as we cannot directly load suite python class from a different venv.
        """
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import (
            AppWorkdirMixin,
        )

        def _found(path: Path) -> bool:
            config = AppWorkdirMixin.get_config_from_path(
                path=path,
            )
            if config:
                if not config.read_config().search("package_suite").is_none():
                    return True

            return False

        suite_path = directory_iterate_parent_dirs(
            path=self.get_path(), condition=_found
        )

        if suite_path:
            return suite_path

        return None
