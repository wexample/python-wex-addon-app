from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

from wexample_filestate.config_value.readme_content_config_value import (
    ReadmeContentConfigValue,
)

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

        workdir_path = self._get_workdir_path()
        search_paths = [
            workdir_path / WORKDIR_SETUP_DIR / "knowledge" / "readme",
        ]

        # Suite-level templates
        suite_path = self._get_suite_workdir_path()
        if suite_path is not None:
            search_paths.append(
                suite_path / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        # Default templates (bundled)
        bundled_path = self._get_bundled_templates_path()
        if bundled_path is not None:
            search_paths.append(bundled_path)

        return search_paths

    def _get_section_names(self) -> list[str]:
        """Return the list of section names to include in the README.

        Default sections common to all packages. Subclasses can override
        to add language-specific sections.

        Returns:
            List of section names in order
        """
        return [
            "title",
            "table-of-contents",
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
            "dependencies": self._get_project_dependencies(),
            "deps_list": self._format_dependencies_list(
                self._get_project_dependencies()
            ),
            "description": self._get_project_description(),
            "homepage": self._get_project_homepage(),
            "license_info": self._get_project_license(),
            "package_name": self._get_package_name(),
            "project_name": self._get_project_name(),
            "version": self._get_project_version(),
            "workdir": self.workdir,
        }

    # Abstract methods for workdir paths
    def _get_workdir_path(self) -> Path:
        """Return the workdir path.

        Default implementation uses self.workdir.get_path().
        """
        return self.workdir.get_path()

    def _get_suite_workdir_path(self) -> Path | None:
        """Return the suite workdir path if available.

        Default implementation uses self.workdir.find_suite_workdir_path().
        """
        return self.workdir.find_suite_workdir_path()

    def _get_bundled_templates_path(self) -> Path | None:
        """Return the path to bundled default templates.

        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement _get_bundled_templates_path()"
        )

    # Abstract methods for project metadata
    def _get_package_name(self) -> str:
        """Return the package name.

        Default implementation uses self.workdir.get_package_name().
        """
        return self.workdir.get_package_name()

    def _get_project_name(self) -> str:
        """Return the project name.

        Default implementation uses self.workdir.get_project_name().
        """
        return self.workdir.get_project_name()

    def _get_project_version(self) -> str:
        """Return the project version.

        Default implementation uses self.workdir.get_project_version().
        """
        return self.workdir.get_project_version()

    def _get_project_description(self) -> str:
        """Return the project description.

        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement _get_project_description()"
        )

    def _get_project_homepage(self) -> str:
        """Return the project homepage URL.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _get_project_homepage()")

    def _get_project_license(self) -> str:
        """Return the project license information.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _get_project_license()")

    def _get_project_dependencies(self) -> list[str]:
        """Return the list of project dependencies.

        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement _get_project_dependencies()"
        )