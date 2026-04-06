from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.config_value.readme_content_config_value import (
    ReadmeContentConfigValue,
)
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from pathlib import Path


@base_class
class AppReadmeConfigValue(ReadmeContentConfigValue):
    """README generation for applications with workdir and suite support.

    Section order is defined by README.tpl.j2, searched across paths in order:
      1. Workdir-specific  (.wex/knowledge/readme/)
      2. Language addon    (bundled in the language-specific wex addon)
      3. App addon         (bundled in wex-addon-app)
      4. Suite parents     (.wex/knowledge/package-readme/, closest first)

    The first README.tpl.j2 found wins. Individual section templates follow
    the same resolution order, so any level can override a single section.
    """

    workdir = public_field(description="The application workdir")

    def _append_template_path_from_module(
        self, module, search_paths: list[str]
    ) -> str | None:
        from wexample_helpers.helpers.module import module_get_path

        """Consider the template directory and the module files are placed at the same relative location into the module directory"""
        template_path = (
            module_get_path(module).parent / "resources" / "readme_templates"
        )

        if template_path.exists():
            search_paths.append(template_path)

    def _get_app_description(self) -> str | None:
        return None

    def _get_app_homepage(self) -> str | None:
        return None

    def _get_dependencies(self) -> dict[str, str]:
        """Extract dependencies from pyproject.toml."""
        return self.workdir.get_dependencies_versions()

    def _get_project_license(self) -> str | None:
        return None

    def _collect_suite_paths(self) -> list[Path]:
        """Return suite paths from closest to farthest."""
        from wexample_helpers.helpers.directory import directory_iterate_parent_dirs
        from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir

        def _is_suite(path: Path) -> bool:
            config = AppWorkdir.get_config_from_path(path=path)
            return bool(
                config and not config.read_config().search("package_suite").is_none()
            )

        suite_paths = []
        current = self.workdir.get_path()
        while True:
            suite_path = directory_iterate_parent_dirs(
                path=current.parent, condition=_is_suite
            )
            if not suite_path:
                break
            suite_paths.append(suite_path)
            current = suite_path

        return suite_paths

    def _get_readme_search_paths(self) -> list[Path]:
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        workdir_path = self.workdir.get_path()
        search_paths = [
            workdir_path / WORKDIR_SETUP_DIR / "knowledge" / "readme",
        ]

        # Language addon bundled templates
        if __name__ != self.__module__:
            self._append_template_path_from_module(
                module=self.__module__, search_paths=search_paths
            )

        # App addon bundled templates
        self._append_template_path_from_module(
            module=__name__, search_paths=search_paths
        )

        for suite_path in self._collect_suite_paths():
            search_paths.append(
                suite_path / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        return search_paths

    def _get_template_context(self) -> dict:
        return {
            # filestate: python-iterable-sort
            "dependencies": self._get_dependencies(),
            "description": self._get_app_description(),
            "homepage": self._get_app_homepage(),
            "license_info": self._get_project_license(),
            "package_name": self.workdir.get_package_name(),
            "project_name": self.workdir.get_project_name(),
            "version": self.workdir.get_project_version(),
            "workdir": self.workdir,
        }
