from wexample_helpers.classes.abstract_method import abstract_method
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

class AppDependenciesConfigFileMixin:
    @abstract_method
    def add_dependency_from_string(
            self,
            package_name: str,
            version: str,
            operator: str = "==",
            optional: bool = False,
            group: None | str = None,
    ) -> bool:
        pass

    def add_dependency(
            self,
            package: CodeBaseWorkdir,
            version: str,
            operator: str = "==",
            optional: bool = False,
            group: None | str = None,
    ) -> bool:
        package_name = package.get_package_dependency_name()
        return self.add_dependency_from_string(
            package_name=package_name,
            version=version,
            operator=operator,
            optional=optional,
            group=group,
        )