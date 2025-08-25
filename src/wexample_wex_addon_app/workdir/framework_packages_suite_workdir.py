from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_package_workdir import FrameworkPackageWorkdir


class FrameworkPackageSuiteWorkdir(ProjectWorkdir):
    def get_local_packages_names(self) -> list[str]:
        return [p.get_package_name() for p in self.get_packages()]

    def build_dependencies_map(self) -> dict[str, list[str]]:
        dependencies = {}
        for package in self.get_packages():
            dependencies[package.get_package_name()] = self.filter_local_packages(package.get_dependencies())

        return dependencies

    def get_packages(self) -> list[FrameworkPackageWorkdir]:
        pip_dir = self.find_by_name(item_name='pip')
        if pip_dir:
            return pip_dir.get_children_list()
        return []

    def get_package(self, package_name: str) -> FrameworkPackageWorkdir | None:
        for package in self.get_packages():
            if package.get_package_name() == package_name:
                return package
        return None

    def filter_local_packages(self, packages: list[str]) -> list[str]:
        """
        Keep only dependencies that are local to this workspace.

        A local dependency is one whose package name matches one of the packages
        discovered by get_packages().
        """
        # Use the dedicated helper to retrieve local package names
        local_names = set(self.get_local_packages_names())
        if not packages:
            return []
        # Return only those present locally, preserve order and remove duplicates
        seen: set[str] = set()
        filtered: list[str] = []
        for name in packages:
            if name in local_names and name not in seen:
                seen.add(name)
                filtered.append(name)
        return filtered

    def build_dependencies_stack(
            self,
            package: FrameworkPackageWorkdir,
            dependency: FrameworkPackageWorkdir,
            dependencies_map: dict[str, list[str]],
    ) -> list[FrameworkPackageWorkdir]:
        """When a package depends on another (uses it in its codebase),
        return the dependency chain to locate the original package that declares the explicit dependency."""
        return []
