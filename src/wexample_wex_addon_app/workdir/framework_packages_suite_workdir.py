from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_filestate.result.file_state_result import FileStateResult
from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.const.types import PathOrString
from wexample_prompt.common.progress.progress_handle import ProgressHandle
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig

    from wexample_wex_addon_app.workdir.code_base_workdir import (
        CodeBaseWorkdir,
    )


class FrameworkPackageSuiteWorkdir(BasicAppWorkdir):
    def _package_title(self, path: PathOrString, message: str):
        self.io.title(f"📦 {path.name}: {message}")

    def packages_execute_shell(
            self,
            cmd: list[str],
    ):
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import (
            AppWorkdirMixin,
        )

        for package_path in self.get_packages_paths():
            self._package_title(
                path=package_path,
                message=f"Executing shell {package_path.name}"
            )

            # Allow interruption
            try:
                if (
                        AppWorkdirMixin.shell_run_from_path(cmd=cmd, path=package_path)
                        is None
                ):
                    self.io.log("Invalid package directory, skipping.", indentation=1)

            except KeyboardInterrupt:
                return

    def apply(self, **kwargs) -> FileStateResult:
        from wexample_filestate.enum.scopes import Scope
        from wexample_wex_core.resolver.addon_command_resolver import (
            AddonCommandResolver,
        )

        from wexample_wex_addon_app.commands.file_state.rectify import (
            app__file_state__rectify,
        )
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import (
            AppWorkdirMixin,
        )

        result = super().apply(**kwargs)

        # Execute "apply" command on package is the same of using rectify app command.
        cmd = [
            AddonCommandResolver.build_command_from_function(
                command_wrapper=app__file_state__rectify
            ),
            "--indentation-level",
            "1",  # TODO How to know current indentation level without access to kernel ?
        ]

        interactive = kwargs.get("interactive", True)
        if interactive is False:
            cmd.append("--yes")

        filter_path = kwargs.get("filter_path", False)
        if filter_path:
            cmd.append("--filter-path")
            cmd.append(filter_path)

        filter_operation = kwargs.get("filter_operation", False)
        if filter_operation:
            cmd.append("--filter-operation")
            cmd.append(filter_operation)

        max = kwargs.get("max", False)
        if max:
            cmd.append("--max")
            cmd.append(max)

        scopes = kwargs.get("scopes", False)
        if scopes and not Scope.REMOTE in scopes:
            cmd.append("--no-remote")

        for package_path in self.get_packages_paths():
            self.io.title(f"📦 Rectifying {package_path.name}")
            # Allow interruption
            try:
                if (
                        AppWorkdirMixin.shell_run_from_path(cmd=cmd, path=package_path)
                        is None
                ):
                    self.io.log("Invalid package directory, skipping.", indentation=1)

            except KeyboardInterrupt:
                return result

        return result

    def build_dependencies_map(self) -> dict[str, list[str]]:
        dependencies = {}
        for package in self.get_packages():
            dependencies[package.get_package_name()] = self.filter_local_packages(
                package.get_dependencies()
            )

        return dependencies

    def build_dependencies_stack(
            self,
            package: CodeBaseWorkdir,
            dependency: CodeBaseWorkdir,
            dependencies_map: dict[str, list[str]],
    ) -> list[CodeBaseWorkdir]:
        """When a package depends on another (uses it in its codebase),
        return the dependency chain to locate the original package that declares the explicit dependency.
        """
        return []

    # Publication planning helpers
    def compute_packages_to_publish(self) -> list[CodeBaseWorkdir]:
        """Return packages that changed since their last publication tag.

        If a package has no previous tag, it is considered to be published.
        """
        to_publish: list[CodeBaseWorkdir] = []
        for pkg in self.get_packages():
            if pkg.has_changes_since_last_publication_tag():
                to_publish.append(pkg)
        return to_publish

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

    def get_dependents(self, package: CodeBaseWorkdir) -> list[CodeBaseWorkdir]:
        return []

    def get_local_packages_names(self) -> list[str]:
        return [p.get_package_name() for p in self.get_packages()]

    def get_ordered_packages(self) -> list[CodeBaseWorkdir]:
        return self.get_packages()

    def get_package(self, package_name: str) -> CodeBaseWorkdir | None:
        for package in self.get_packages():
            if package.get_package_name() == package_name:
                return package
        return None

    def get_packages(self) -> list[CodeBaseWorkdir]:
        pip_dir = self.find_by_name(item_name="pip")
        if pip_dir:
            return pip_dir.get_children_list()
        return []

    def get_packages_paths(self) -> list[Path]:
        """Return all resolved package paths that are directories only."""
        config = self.get_config().search("package_suite.location").get_list()

        resolved: list[Path] = []

        for location in (loc.get_str() for loc in config):
            for path in self.get_path().glob(location):
                if path.is_dir():  # ✅ only keep directories
                    resolved.append(path)

        return resolved

    def packages_propagate_versions(
            self, progress: ProgressHandle | None = None
    ) -> None:
        ordered_packages = self.get_ordered_packages()

        progress = (
                progress
                or self.io.progress(
            label=f"Starting...", total=len(ordered_packages)
        ).get_handle()
        )

        for package in ordered_packages:
            progress.advance(
                label=f'Propagating package "{package.get_package_name()}" version "{package.get_project_version()}"',
                step=1,
            )
            self.io.indentation_up()
            for dependent in self.get_dependents(package):
                self.io.log(f"Applying to {dependent.get_package_name()}")
                dependent.save_dependency(package)
            self.io.indentation_down()
        progress.finish()

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.children_filter_option import (
            ChildrenFilterOption,
        )

        raw_value = super().prepare_value(raw_value=raw_value)

        children = raw_value["children"]

        # By default, consider each sub folder as a pip package
        children.append(
            {
                "name": self._get_children_package_directory_name(),
                "type": DiskItemType.DIRECTORY,
                "children": [
                    ChildrenFilterOption(
                        filter=self._child_is_package_directory,
                        pattern={
                            "class": self._get_children_package_workdir_class(),
                            "type": DiskItemType.DIRECTORY,
                        },
                    )
                ],
            }
        )

        return raw_value

    @abstract_method
    def _child_is_package_directory(self, entry: Path) -> bool:
        pass

    def _get_children_package_directory_name(self) -> str:
        return "packages"

    def _get_children_package_workdir_class(self) -> type[CodeBaseWorkdir]:
        from wexample_wex_addon_app.workdir.code_base_workdir import (
            CodeBaseWorkdir,
        )

        return CodeBaseWorkdir
