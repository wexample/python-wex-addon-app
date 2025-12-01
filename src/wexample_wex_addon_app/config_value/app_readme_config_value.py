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

    def _get_bundled_templates_path(self):
        """Return path to bundled Python README templates."""
        from pathlib import Path

        return Path(__file__).parent.parent / "resources" / "readme_templates"

    def _get_project_description(self) -> str:
        """Extract description from pyproject.toml."""
        return self._get_project_config().get("description", "")

    def _get_project_dependencies(self) -> list[str]:
        """Extract dependencies from pyproject.toml."""
        return self._get_project_config().get("dependencies", [])

    def _get_project_homepage(self) -> str:
        """Extract homepage URL from pyproject.toml."""
        project = self._get_project_config()
        urls = (
            project.get("urls", {}) if isinstance(project.get("urls", {}), dict) else {}
        )
        return urls.get("homepage") or urls.get("Homepage") or ""

    def _get_project_config(self) -> dict:
        """Get the pyproject.toml configuration.

        Returns:
            The project configuration dictionary
        """
        doc = self.workdir.get_project_config()
        return doc.get("project", {}) if isinstance(doc, dict) else {}

    def _get_project_license(self) -> str:
        """Extract license information from pyproject.toml."""
        project = self._get_project_config()
        license_field = project.get("license", {})
        if isinstance(license_field, dict):
            return license_field.get("text", "") or license_field.get("file", "")
        return str(license_field) if license_field else ""

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

        # Default templates (bundled)
        bundled_path = self._get_bundled_templates_path()
        if bundled_path is not None:
            search_paths.append(bundled_path)

        def _get_template(workdir):
            search_paths.append(
                workdir.get_path() / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        self.workdir.collect_stack_in_suites_tree(callback=_get_template)

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
            "package_name": self.workdir.get_package_name(),
            "project_name": self.workdir.get_project_name(),
            "version": self.workdir.get_project_version(),
            "workdir": self.workdir,
        }
