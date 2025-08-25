from __future__ import annotations

from abc import abstractmethod

from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class FrameworkPackageWorkdir(ProjectWorkdir):
    @abstractmethod
    def get_package_name(self) -> str:
        pass

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        pass

    def imports_package_in_codebase(self, searched_package: FrameworkPackageWorkdir) -> bool:
        """Check whether the given package is used in this package's codebase."""
        return False

    def build_dependencies_stack(
            self,
            package: FrameworkPackageWorkdir,
            dependency: FrameworkPackageWorkdir) -> list[FrameworkPackageWorkdir]:
        """When package is dependent from another one (is using it in its codebase),
        list the packages inheritance stack to find the original package declaring the explicit dependency"""
        return []
