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

    Sections are discovered automatically from template files. Order is
    controlled via `readme.sections` in any suite's config.yml — sections
    listed there appear first, the rest follow in discovery order.

    Search path priority (first match wins per section):
      1. Workdir-specific  (.wex/knowledge/readme/)
      2. Language addon    (bundled in the language wex addon)
      3. App addon         (bundled in wex-addon-app)
      4. Suite parents     (.wex/knowledge/package-readme/, closest first)
    """

    workdir = public_field(description="The application workdir")

    def _append_template_path_from_module(self, module, search_paths: list) -> None:
        from wexample_helpers.helpers.module import module_get_path

        """Consider the template directory and the module files are placed at the same relative location into the module directory"""
        try:
            template_path = (
                module_get_path(module).parent / "resources" / "readme_templates"
            )
        except TypeError:
            # module_get_path() raises TypeError when the module isn't a package
            # (single-file modules like config_value submodules) — those have no
            # template dir to contribute, just skip them.
            return
        if template_path.exists():
            search_paths.append(template_path)

    def _collect_suite_paths(self) -> list[Path]:
        """Return suite paths from closest to farthest."""
        from wexample_helpers.helpers.directory import directory_iterate_parent_dirs

        from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

        def _is_suite(path: Path) -> bool:
            config = ManagedWorkdir.get_config_from_path(path=path)
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

    def _discover_sections(self) -> list[str]:
        """Scan all search paths for .md.j2 and .md files, deduplicating."""
        seen: set[str] = set()
        sections: list[str] = []

        for search_path in self._get_readme_search_paths():
            if not search_path.exists():
                continue
            for entry in sorted(search_path.iterdir()):
                if not entry.is_file():
                    continue
                name = entry.name
                if name.startswith("_"):
                    continue
                if name.endswith(".md.j2"):
                    section = name[: -len(".md.j2")]
                elif name.endswith(".md"):
                    section = name[: -len(".md")]
                else:
                    continue
                if section not in seen:
                    seen.add(section)
                    sections.append(section)

        return sections

    def _get_app_description(self) -> str | None:
        return None

    def _get_app_homepage(self) -> str | None:
        return None

    def _get_dependencies(self) -> dict[str, str]:
        return self.workdir.get_dependencies_versions()

    def _get_project_license(self) -> str | None:
        return None

    def _get_readme_search_paths(self) -> list[Path]:
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        workdir_path = self.workdir.get_path()
        search_paths = [
            workdir_path / WORKDIR_SETUP_DIR / "knowledge" / "readme",
        ]

        if __name__ != self.__module__:
            self._append_template_path_from_module(
                module=self.__module__, search_paths=search_paths
            )

        self._append_template_path_from_module(
            module=__name__, search_paths=search_paths
        )

        for suite_path in self._collect_suite_paths():
            search_paths.append(
                suite_path / WORKDIR_SETUP_DIR / "knowledge" / "package-readme"
            )

        return search_paths

    def _get_section_names(self) -> list[str]:
        """Discover sections from template files, ordered by suite config.yml.

        Any suite can declare ordering via:
            readme:
              sections:
                - title
                - installation
                - quickstart

        Listed sections appear first. Discovered but unlisted sections follow
        in discovery order. The closest suite's ordering takes precedence.
        """
        discovered = self._discover_sections()
        order = self._read_suite_section_order()
        return self._merge_section_order(discovered, order)

    def _get_template_context(self) -> dict:
        return {
            # filestate: python-iterable-sort
            "dependencies": self._get_dependencies(),
            "description": self._get_app_description(),
            "homepage": self._get_app_homepage(),
            "license_info": self._get_project_license(),
            "package_name": self.workdir.get_project_name(),
            "project_name": self.workdir.get_project_name(),
            "version": self.workdir.get_setup_version(),
            "workdir": self.workdir,
        }

    def _merge_section_order(
        self, discovered: list[str], order: list[str]
    ) -> list[str]:
        """Pin title/table-of-contents first, apply order to the rest.

        title and table-of-contents are structural anchors always rendered
        first regardless of config. Everything else is driven by
        readme.sections in the suite config.yml.
        """
        pinned = {"title", "table-of-contents"}
        first = [s for s in ["title", "table-of-contents"] if s in discovered]
        rest = [s for s in discovered if s not in pinned]

        ordered = [s for s in order if s in rest]
        remainder = [s for s in rest if s not in set(order)]

        return first + ordered + remainder

    def _read_suite_section_order(self) -> list[str]:
        """Read readme.sections from suite configs, closest suite wins."""
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        from wexample_wex_addon_app.item.file.app_config_yaml_file import (
            AppConfigYamlFile,
        )

        order: list[str] = []
        for suite_path in reversed(self._collect_suite_paths()):
            config_file = suite_path / WORKDIR_SETUP_DIR / "config.yml"
            if not config_file.exists():
                continue
            config = AppConfigYamlFile.create_from_path(
                path=config_file
            ).read_parsed()
            if not config:
                continue
            suite_order = config.get("readme", {}).get("sections", [])
            if suite_order:
                order = [s for s in suite_order if isinstance(s, str)]

        return order
