from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.const.types import PathOrString
from wexample_wex_core.resolver.addon_command_resolver import AddonCommandResolver

from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig

    from wexample_wex_addon_app.workdir.code_base_workdir import (
        CodeBaseWorkdir,
    )
    from wexample_wex_addon_app.workdir.mixin.with_suite_tree_workdir_mixin import (
        WithSuiteTreeWorkdirMixin,
    )


class FrameworkPackageSuiteWorkdir(BasicAppWorkdir):
    def build_dependencies_map(self) -> dict[str, list[str]]:
        dependencies = {}
        for package in self.get_packages():
            dependencies[package.get_package_name()] = self.filter_local_packages(
                package.get_dependencies_versions().keys()
            )

        return dependencies

    def build_dependencies_stack(
        self,
        package: CodeBaseWorkdir,
        dependency: CodeBaseWorkdir,
        dependencies_map: dict[str, list[str]],
    ) -> list[CodeBaseWorkdir]:
        """Return the declared dependency chain from `package` to `dependency`.

        Deterministic DFS on the local dependencies map. Returns a list of
        package objects [package, ..., dependency] or an empty list if no path exists.
        """
        start = package.get_package_name()
        target = dependency.get_package_name()

        if start == target:
            return [package]

        # Ensure both nodes exist in the map
        nodes = set(dependencies_map.keys()) | {
            d for deps in dependencies_map.values() for d in deps
        }
        if start not in nodes or target not in nodes:
            return []

        visited: set[str] = set()
        stack: list[tuple[str, list[str]]] = [(start, [start])]

        while stack:
            current, path = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            for neighbor in sorted(dependencies_map.get(current, [])):
                if neighbor in visited:
                    continue
                new_path = path + [neighbor]
                if neighbor == target:
                    chain: list[CodeBaseWorkdir] = []
                    for name in new_path:
                        pkg = self.get_package(name)
                        if pkg is not None:
                            chain.append(pkg)
                    if chain and chain[-1].get_package_name() == target:
                        return chain
                stack.append((neighbor, new_path))

        return []

    def build_ordered_dependencies(self) -> list[str]:
        """Return package names ordered leaves -> trunk."""
        return self.topological_order(self.build_dependencies_map())

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
        dependents = []
        for neighbor_package in self.get_packages():
            if neighbor_package.depends_from(package):
                dependents.append(neighbor_package)
        return dependents

    def get_local_packages_names(self) -> list[str]:
        return [p.get_package_name() for p in self.get_packages()]

    def get_ordered_packages(self) -> list[CodeBaseWorkdir]:
        order = self.build_ordered_dependencies()
        by_name = {p.get_package_name(): p for p in self.get_packages()}
        return [by_name[name] for name in order if name in by_name]

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

    def packages_execute_function(
        self,
        command: callable,
        arguments: list[str] | None = None,
        force: bool = False,
    ) -> None:
        """
        Execute a Python command function (addon command) on all packages.

        This automatically builds the corresponding manager command
        using AddonCommandResolver.

        Example:
            self.packages_execute_function(
                command=app__setup__install,
                arguments=["--env", env],
            )
        """
        resolved_command = AddonCommandResolver.build_command_from_function(
            command_wrapper=command
        )

        self.packages_execute_manager(
            command=resolved_command,
            arguments=arguments,
            force=force,
        )

    def packages_execute_manager(
        self,
        command: str,
        arguments: list[str] | None = None,
        force: bool = False,
    ) -> None:
        """Execute a manager command on all packages."""
        self._packages_execute(
            cmd=[command] + (arguments or []),
            executor_method=BasicAppWorkdir.manager_run_from_path,
            message="Executing command",
            force=force,
        )

    def packages_execute_shell(self, cmd: list[str], force: bool = False) -> None:
        """Execute a raw shell command on all packages."""
        self._packages_execute(
            cmd=cmd,
            executor_method=BasicAppWorkdir.shell_run_from_path,
            message="Executing shell",
            force=force,
        )

    def packages_validate_internal_dependencies_declarations(self) -> None:
        """Ensure imports match declared local dependencies."""
        from wexample_wex_addon_app.exception.dependency_violation_exception import (
            DependencyViolationException,
        )

        dependencies_map = self.build_dependencies_map()

        self.io.log("Checking packages dependencies consistency...")
        self.io.indentation_up()
        progress = self.io.progress(
            total=len(dependencies_map), print_response=False
        ).get_handle()

        for package_name in dependencies_map:
            package = self.get_package(package_name)
            if package is None:
                continue

            search_fn = getattr(package, "search_imports_in_codebase", None)
            if not callable(search_fn):
                progress.advance(
                    label=f"Package {package.get_project_name()} (no search)", step=1
                )
                continue

            for package_name_search in dependencies_map:
                searched_package = self.get_package(package_name_search)
                if searched_package is None:
                    continue

                imports = search_fn(searched_package)
                if len(imports) == 0:
                    continue

                dependencies_stack = self.build_dependencies_stack(
                    package, searched_package, dependencies_map
                )

                if len(dependencies_stack) == 0:
                    import_locations = [
                        f"{res.item.get_path()}:{res.line}:{res.column}"
                        for res in imports
                    ]
                    raise DependencyViolationException(
                        package_name=package_name,
                        imported_package=package_name_search,
                        import_locations=import_locations,
                    )

            progress.advance(label=f"Package {package.get_project_name()}", step=1)

        self.io.success("Internal dependencies match.")
        self.io.indentation_down()

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        """Prepare file state configuration for package suite."""
        raw_value = super().prepare_value(raw_value=raw_value)

        children = raw_value["children"]
        base_path = Path(self.get_path()).resolve()
        package_paths = self.get_packages_paths()

        from wexample_filestate.const.disk import DiskItemType

        # Root of the generated tree
        tree: dict = {
            "name": base_path.name,
            "type": DiskItemType.DIRECTORY,
            "children": {},
        }

        for package_path in package_paths:
            package_path = package_path.resolve()

            # Skip invalid paths
            if not BasicAppWorkdir.is_app_workdir_path(path=package_path):
                continue

            # Build relative path between the configured root and the package path
            rel_parts = list(package_path.relative_to(base_path).parts)

            # Walk the tree structure and create missing nodes
            current = tree
            for part in rel_parts[:-1]:  # all intermediate directories
                current = current["children"].setdefault(
                    part,
                    {
                        "name": part,
                        "type": DiskItemType.DIRECTORY,
                        "children": {},
                    },
                )

            # Add final package directory
            leaf_name = rel_parts[-1]
            current["children"][leaf_name] = {
                "name": leaf_name,
                "class": self._get_children_package_workdir_class(),
                "type": DiskItemType.DIRECTORY,
                "active": False,
                "children": {},  # packages may also contain children later
            }

        # Convert "children" dicts → lists (required format)
        def normalize(node: dict) -> dict:
            if isinstance(node.get("children"), dict):
                node["children"] = [
                    normalize(child) for child in node["children"].values()
                ]
            return node

        # Only append children of the generated root (not the root itself)
        children.extend(normalize(tree)["children"])

        return raw_value

    def propagate_packages_versions(self) -> None:
        for package in self.get_ordered_packages():
            self.propagate_version_of(package=package)

    def propagate_version_of(self, package: WithSuiteTreeWorkdirMixin) -> None:
        package.log(f"Propagating version {package.get_project_version()}", prefix=True)
        package.io.indentation_up()

        for dependent in self.get_dependents(package):
            updated = dependent.save_dependency_from_package(package)
            if updated:
                package.log(
                    f"Updated {dependent.get_project_name()} dependencies",
                )

        package.success("Packages version has been propagated across suite")
        package.io.indentation_down()

    def publish_dependencies(self) -> dict[str, str]:
        """The suite provides dependency of package it manages."""
        dependencies = {}

        for package in self.get_packages():
            dependencies[package.get_package_name()] = package.get_project_version()

        return dependencies

    def setup_install(self, env: str | None = None, force: bool = False) -> None:
        from wexample_wex_addon_app.commands.setup.install import app__setup__install

        self.subtitle(f"Installing suite app")
        super().setup_install(env=env)

        self.subtitle(f"Installing local packages")
        for package in self.get_packages():
            package.ensure_app_manager_setup()

        self.packages_execute_function(
            command=app__setup__install,
            arguments=["--env", env],
        )

    def topological_order(self, dep_map: dict[str, list[str]]) -> list[str]:
        """Deterministic topological order (leaves -> trunk) using graphlib."""
        from graphlib import CycleError, TopologicalSorter

        # Normalize: include every mentioned node and sort for stable results
        nodes = set(dep_map.keys()) | {d for deps in dep_map.values() for d in deps}
        normalized: dict[str, list[str]] = {
            key: sorted([dep for dep in dep_map.get(key, []) if dep in nodes])
            for key in sorted(nodes)
        }

        ts = TopologicalSorter()
        for key, deps in normalized.items():
            ts.add(key, *deps)

        try:
            order = list(ts.static_order())
        except CycleError as err:
            msg = getattr(err, "args", [None])[0] or "Cyclic dependencies detected"
            raise ValueError(str(msg)) from err

        # Return only local packages (original keys of dep_map)
        return [name for name in order if name in dep_map]

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

        self.title(f"📦 {message}: {path.name}")
        self.log(f"Path: {cli_make_clickable_path(path)}", indentation=1)

    def _packages_execute(
        self,
        cmd: list[str],
        executor_method: callable,
        message: str,
        force: bool = False,
    ) -> None:
        """
        Generic method to execute a command on all detected packages.

        Args:
            cmd: Command to execute (as a list of strings)
            executor_method: Method used to execute the command (e.g. manager_run_from_path, shell_run_from_path)
            message: Displayed title message
            force: If True, run even if directory is not recognized as an app workdir
        """
        import shlex

        from wexample_prompt.enums.terminal_color import TerminalColor

        for package_path in self.get_packages_paths():
            if not force and not BasicAppWorkdir.is_app_workdir_path(path=package_path):
                continue

            self._package_title(path=package_path, message=message)
            self.log(f"Command: {shlex.join(cmd)}", indentation=1)
            self.separator(color=TerminalColor.BLACK)

            try:
                result = executor_method(cmd=cmd, path=package_path)
                if result is None:
                    self.log("Invalid package directory, skipping.", indentation=1)
            except Exception as e:
                self.log(f"Error executing command: {e}", indentation=1)
                return

            self.separator(color=TerminalColor.BLACK)
