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

    This class handles all common operations for app-based READMEs:
    - Workdir-based template search paths
    - Suite-level template inheritance
    - Predefined section list
    - Common project metadata extraction

    Subclasses only need to implement language-specific methods.
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

    def _get_readme_search_paths(self) -> list[Path]:
        """Return list of paths to search for README templates.

        Searches in order:
        1. Workdir-specific templates
        2. Suite-level templates (if available)
        3. Bundled default templates

        Returns:
            List of paths to search for templates
        """
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        workdir_path = self.workdir.get_path()
        search_paths = [
            workdir_path / WORKDIR_SETUP_DIR / "knowledge" / "readme",
        ]

        # Language package specific template
        if __name__ != self.__module__:
            self._append_template_path_from_module(
                module=self.__module__, search_paths=search_paths
            )

        # App package template
        self._append_template_path_from_module(
            module=__name__, search_paths=search_paths
        )

        def _get_template(workdir) -> None:
            search_paths.append(
                workdir.get_path() / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        search_paths.extend(
            self.workdir.collect_stack_in_suites_tree(
                callback=_get_template, include_self=False
            )
        )

        return search_paths

    def _get_section_names(self) -> list[str]:
        """Return the list of section names to include in the README.

        Default sections common to all packages. Subclasses can override
        to add language-specific sections.

        Returns:
            List of section names in order
        """
        return super()._get_section_names() + [
            "status-compatibility",
            "prerequisites",
            "installation",
            "quickstart",
            "basic-usage",
            "configuration",
            "logging",
            "api-reference",
            "examples",
            "tests",
            "code-quality",
            "versioning",
            "changelog",
            "migration-notes",
            "roadmap",
            "troubleshooting",
            "security",
            "privacy",
            "support",
            "contribution-guidelines",
            "maintainers",
            "license",
            "useful-links",
            "suite-integration",
            "compatibility-matrix",
            "requirements",
            "dependencies",
            "links",
            "suite-signature",
        ]

    def _get_template_context(self) -> dict:
        """Build the template context with all variables.

        Common variables for all app-based READMEs. Subclasses should
        override and call super() to add language-specific variables.

        Returns:
            Dictionary of template variables
        """
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
