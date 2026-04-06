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
        """Return list of paths to search for README templates.

        Searches in order:
        1. Workdir-specific templates
        2. Language addon bundled templates
        3. App addon bundled templates
        4. Suite-level templates (closest to farthest)

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

        for suite_path in self._collect_suite_paths():
            search_paths.append(
                suite_path / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        return search_paths

    def _get_section_names(self) -> list[str]:
        """Return the ordered list of section names to include in the README.

        Base sections are defined here. Suite configs (config.yml) can inject
        additional sections via a `readme.sections` key:

            readme:
              sections:
                - name: my-section
                  after: license      # insert after this section
                - name: other
                  before: useful-links  # or before

        Suites are processed farthest-first so closer suites take precedence.

        Returns:
            List of section names in order
        """
        base = super()._get_section_names() + [
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
        return self._apply_suite_section_injections(base)

    def _apply_suite_section_injections(self, sections: list[str]) -> list[str]:
        """Inject sections declared in suite configs into the section list.

        Processes suite configs farthest-first so the closest suite has the
        final say on positioning.
        """
        import yaml
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        for suite_path in reversed(self._collect_suite_paths()):
            config_file = suite_path / WORKDIR_SETUP_DIR / "config.yml"
            if not config_file.exists():
                continue

            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                continue

            for injection in config.get("readme", {}).get("sections", []):
                if isinstance(injection, str):
                    name, after, before = injection, None, None
                else:
                    name = injection.get("name")
                    after = injection.get("after")
                    before = injection.get("before")

                if not name or name in sections:
                    continue

                if after and after in sections:
                    sections.insert(sections.index(after) + 1, name)
                elif before and before in sections:
                    sections.insert(sections.index(before), name)
                else:
                    sections.append(name)

        return sections

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
