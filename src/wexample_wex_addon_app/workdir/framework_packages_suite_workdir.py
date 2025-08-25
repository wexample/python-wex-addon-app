from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.workdir.project_workdir import ProjectWorkdir

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_package_workdir import FrameworkPackageWorkdir


class FrameworkPackageSuiteWorkdir(ProjectWorkdir):
    def get_local_packages_names(self) -> list[str]:
        return [p.get_package_name() for p in self.get_packages()]

    def build_dependencies(self) -> dict[str, list[str]]:
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
