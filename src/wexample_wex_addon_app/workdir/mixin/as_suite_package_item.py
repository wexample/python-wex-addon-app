from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@base_class
class AsSuitePackageItem(BaseClass):
    @classmethod
    @abstract_method
    def _get_children_package_workdir_class(cls) -> type[FrameworkPackageSuiteWorkdir]:
        pass

    def find_suite_workdir_path(self) -> Path | None:
        """
        We have to trust the configuration file to know if parent directory is a suite or not,
        as we cannot directly load suite python class from a different venv.
        """
        from wexample_helpers.helpers.directory import directory_iterate_parent_dirs
        from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

        source_path = self.get_path()

        def _found(path: Path) -> bool:
            config = BasicAppWorkdir.get_config_from_path(
                path=path,
            )
            if config:
                if not config.read_config().search("package_suite").is_none():
                    return True

            return False

        suite_path = directory_iterate_parent_dirs(
            path=source_path,
            condition=_found
        )

        if suite_path and suite_path != source_path:
            return suite_path

        return None

    def get_env_parameter_or_suite_fallback(
        self, key: str, default: str | None = None
    ) -> str | None:
        value = self.get_env_parameter(
            key=key,
            default=default,
        )

        if value is None:
            suite_workdir = self.get_suite_workdir()
            if suite_workdir:
                return suite_workdir.get_env_parameter(
                    key=key,
                    default=default,
                )
        return value

    def get_suite_workdir(self) -> None | FrameworkPackageSuiteWorkdir:
        suite_path = self.find_suite_workdir_path()

        if suite_path and suite_path.exists():
            suite = self._get_children_package_workdir_class().create_from_path(
                path=suite_path
            )
            return suite

        return None

    def search_in_package_or_suite_config(self, key: str):
        """Search for a config value in the package config, fallback to suite config if not found."""
        value = self.get_config().search(key)

        if value.is_none():
            suite_workdir = self.get_suite_workdir()
            if suite_workdir:
                return suite_workdir.get_config().search(key)

        return value
