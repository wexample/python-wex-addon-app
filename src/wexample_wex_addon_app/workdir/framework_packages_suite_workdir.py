from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.const.types import PathOrString
from wexample_prompt.common.progress.progress_handle import ProgressHandle
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir
from wexample_wex_core.context.execution_context import ExecutionContext

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig
    from wexample_wex_addon_app.workdir.code_base_workdir import (
        CodeBaseWorkdir,
    )


class FrameworkPackageSuiteWorkdir(BasicAppWorkdir):
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
        return self.find_all_by_type(
            class_type=self._get_children_package_workdir_class(), recursive=True
        )

    def get_packages_paths(self) -> list[Path]:
        """Return all resolved package paths that are directories only."""
        config = self.get_config().search("package_suite.location").get_list()

        resolved: list[Path] = []

        for location in (loc.get_str() for loc in config):
            for path in self.get_path().glob(location):
                if path.is_dir():  # ✅ only keep directories
                    resolved.append(path)

        return resolved

    def packages_execute_manager(
        self,
        command: str,
        context: ExecutionContext,
        arguments: None | list[str] = None,
    ) -> None:
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import (
            AppWorkdirMixin,
        )

        cmd = [command]
        arguments = arguments or []

        if arguments is not None:
            cmd.extend(arguments)

        if "--indentation-level" not in cmd:
            cmd.extend(["--indentation-level", str(context.io.indentation + 1)])

        self._packages_execute(
            cmd=cmd,
            executor_method=AppWorkdirMixin.manager_run_from_path,
            message="Executing command",
        )

    def packages_execute_shell(self, cmd: list[str]) -> None:
        from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import (
            AppWorkdirMixin,
        )

        self._packages_execute(
            cmd=cmd,
            executor_method=AppWorkdirMixin.shell_run_from_path,
            message="Executing shell",
        )

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
        """Prepare file state configuration for package suite.

        Builds a recursive tree structure of directories containing packages,
        based on package_suite.location patterns from config.yml.
        """
        raw_value = super().prepare_value(raw_value=raw_value)

        children = raw_value["children"]

        # Get all package paths from configured locations
        package_paths = self.get_packages_paths()

        # Build a tree structure from the package paths
        tree = self._build_directory_tree(package_paths)

        # Convert tree to config format and add to children
        children.extend(tree)

        return raw_value

    def _build_directory_tree(self, package_paths: list[Path]) -> list[dict]:
        """Build a recursive directory tree structure from package paths.

        Args:
            package_paths: List of absolute paths to packages

        Returns:
            List of directory nodes in the format:
            [{"name": "dir", "type": "directory", "children": [...]}, ...]
        """
        from wexample_filestate.const.disk import DiskItemType

        # Get the suite root path
        suite_root = self.get_path()

        # Build tree directly in final format
        root_nodes: dict[str, dict] = {}

        for package_path in package_paths:
            # Get relative path from suite root
            try:
                rel_path = package_path.relative_to(suite_root)
            except ValueError:
                # Package is outside suite root, skip it
                continue

            # Navigate/create the tree structure
            parts = rel_path.parts
            current_level = root_nodes

            for i, part in enumerate(parts):
                if part not in current_level:
                    node_config = {
                        "name": part,
                        "type": DiskItemType.DIRECTORY,
                        "children": {},
                    }

                    # If this is the last part (the package itself), add the class
                    if i == len(parts) - 1 and BasicAppWorkdir.is_app_workdir_path(
                        path=package_path
                    ):
                        node_config["class"] = (
                            self._get_children_package_workdir_class()
                        )

                    current_level[part] = node_config

                # Navigate to children for next iteration
                current_level = current_level[part]["children"]

        # Convert children dicts to lists recursively
        def finalize_node(node: dict) -> dict:
            if node["children"]:
                node["children"] = [
                    finalize_node(child) for child in node["children"].values()
                ]
            else:
                # Remove empty children dict
                del node["children"]
            return node

        return [finalize_node(node) for node in root_nodes.values()]

    @abstract_method
    def _child_is_package_directory(self, entry: Path) -> bool:
        pass

    def _create_package_workdir(self, package_path: Path) -> CodeBaseWorkdir | None:
        """Create a workdir instance for a package at the given path.

        This method should be overridden by subclasses to return the appropriate
        workdir type (e.g., PythonPackageWorkdir).
        """
        from wexample_filestate.utils.file_state_manager import FileStateManager

        # Get the workdir class from the child implementation
        self._get_children_package_workdir_class()

        # Check if this path is a valid package directory
        if not self._child_is_package_directory(package_path):
            return None

        # Create the workdir instance
        return FileStateManager.create_from_path(
            path=package_path,
            config={},
            io=self.io,
        )

    def _get_children_package_directory_name(self) -> str:
        return "packages"

    def _get_children_package_workdir_class(self) -> type[CodeBaseWorkdir]:
        from wexample_wex_addon_app.workdir.code_base_workdir import (
            CodeBaseWorkdir,
        )

        return CodeBaseWorkdir

    def _package_title(self, path: PathOrString, message: str) -> None:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        self.io.title(f"📦 {message}: {path.name}")
        self.io.log(f"Path: {cli_make_clickable_path(path)}", indentation=1)

    def _packages_execute(
        self,
        cmd: list[str],
        executor_method: callable,
        message: str,
    ) -> None:
        """Generic method to execute a command on all packages.

        Args:
            cmd: Command to execute
            executor_method: Method to call for execution (e.g., manager_run_from_path or shell_run_from_path)
            message: Message to display in the title
        """
        for package_path in self.get_packages_paths():
            self._package_title(path=package_path, message=message)

            # Allow interruption
            try:
                if executor_method(cmd=cmd, path=package_path) is None:
                    self.io.log("Invalid package directory, skipping.", indentation=1)
            except KeyboardInterrupt:
                return
