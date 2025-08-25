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

    def ensure_dependency_declaration(self, searched_package: FrameworkPackageWorkdir) -> bool:
        """Search if package is used in the current one, and update dependencies if not declared into."""
        return True