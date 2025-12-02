from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wexample_config.config_value.config_value import ConfigValue
from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@base_class
class WithSuiteTreeWorkdirMixin(BaseClass):
    _suite_workdir: None | False | FrameworkPackageSuiteWorkdir = public_field(
        default=None, description="Cache reference to the parent suite"
    )
    _suite_workdir_path: None | False | Path = public_field(
        default=None, description="Cache reference to the parent suite"
    )

    def collect_stack_in_suites_tree(
        self, callback: Callable[[Any], Any], include_self: bool = True
    ) -> list[Any]:
        """
        Walk the suite tree from the current workdir and collect callback results.
        Optionally ignore the current workdir ("self") as starting point.
        """
        workdir = self if include_self else self.get_shallow_suite_workdir()
        stack: list[Any] = []

        while workdir:
            result = callback(workdir)
            if result is not None:
                stack.append(result)

            workdir = workdir.get_shallow_suite_workdir()

        return stack

    def find_suite_workdir_path(self) -> Path | None:
        """
        We have to trust the configuration file to know if parent directory is a suite or not,
        as we cannot directly load suite python class from a different venv.
        """
        from wexample_helpers.helpers.directory import directory_iterate_parent_dirs

        from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

        if self._suite_workdir_path is None:
            source_path = self.get_path()
            self._suite_workdir_path = False

            def _found(path: Path) -> bool:
                config = BasicAppWorkdir.get_config_from_path(
                    path=path,
                )
                if config:
                    if not config.read_config().search("package_suite").is_none():
                        return True

                return False

            suite_path = directory_iterate_parent_dirs(
                path=source_path.parent, condition=_found
            )

            if suite_path and suite_path != source_path:
                self._suite_workdir_path = suite_path

        return self._suite_workdir_path

    def get_env_parameter_or_suite_fallback(
        self, key: str, default: str | None = None
    ) -> str | None:
        value = self.get_env_parameter(
            key=key,
            default=default,
        )

        if value is None:
            suite_workdir = self.get_shallow_suite_workdir()
            if suite_workdir:
                return suite_workdir.get_env_parameter(
                    key=key,
                    default=default,
                )
        return value

    def get_shallow_suite_workdir(self) -> False | FrameworkPackageSuiteWorkdir:
        suite_path = self.find_suite_workdir_path()

        if suite_path and suite_path.exists():
            return self._get_suite_package_workdir_class().create_from_path(
                path=suite_path, configure=False
            )

    def get_suite_workdir(
        self, reload: bool = False
    ) -> False | FrameworkPackageSuiteWorkdir:
        if reload or self._suite_workdir is None:
            suite_path = self.find_suite_workdir_path()
            self._suite_workdir = False

            if suite_path and suite_path.exists():
                self._suite_workdir = (
                    self._get_suite_package_workdir_class().create_from_path(
                        path=suite_path
                    )
                )

        return self._suite_workdir

    def get_vendor_name(self) -> str:
        return self.search_in_package_or_suite_config(
            "global.vendor"
        ).get_str_or_default(default="acme")

    def propagate_version(self) -> None:
        self.get_suite_workdir().propagate_version_of(package=self)

    def save_dependency_from_package(
        self, package: FrameworkPackageSuiteWorkdir
    ) -> bool:
        """Add a dependency from another package, use strict version as this is the intended internal management."""
        return self.save_dependency(
            package_name=package.get_package_name(),
            version=package.get_project_version(),
        )

    def search_closest_in_suites_tree(self, callback) -> Any:
        workdir = self

        while workdir:
            result = callback(workdir)
            if result is not None:
                return result

            workdir = workdir.get_shallow_suite_workdir()

        return None

    def search_in_package_or_suite_config(self, key: str) -> ConfigValue:
        """Search for a config value in the package config, fallback to suite config if not found."""
        from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

        value = self.get_config().search(key)

        if value.is_empty():
            suite_path = self.find_suite_workdir_path()
            if suite_path:
                # Also avoid using children tree as method may be executed before configuration process.
                suite_config_file = BasicAppWorkdir.get_config_from_path(
                    path=suite_path,
                )

                if suite_config_file:
                    return suite_config_file.read_config().search(key)

        return value
