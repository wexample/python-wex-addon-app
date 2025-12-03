from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from wexample_app.const.env import ENV_NAME_PROD
from wexample_app.const.globals import APP_PATH_APP_MANAGER
from wexample_config.config_value.config_value import ConfigValue
from wexample_file.helper.line import line_count_recursive
from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType
from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers_git.helpers.git import git_has_changes_since_tag
from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_wex_core.workdir.workdir import Workdir

from wexample_wex_addon_app.const.path import APP_PATH_TEST
from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig
    from wexample_filestate.result.file_state_result import FileStateResult

    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@base_class
class BasicAppWorkdir(AppWorkdirMixin, Workdir):
    def app_install(self, env: str | None = None, force: bool = False) -> bool:
        return True

    def apply(
        self,
        force: bool = False,
        scopes=None,
        filter_path: str | None = None,
        filter_operation: str | None = None,
        max: int = None,
        **kwargs,
    ) -> FileStateResult:
        from wexample_filestate.result.file_state_result import FileStateResult
        from wexample_helpers.helpers.repo import repo_get_state, repo_has_changed_since

        # Hash protection is only active when all filter parameters are None
        # to avoid false positives when apply behavior is modified by parameters
        hash_protection_active = (
            scopes is None
            and filter_path is None
            and filter_operation is None
            and max is None
        )

        registry_file = self.get_registry_file()
        registry = registry_file.read_config()
        last_update_hash = registry.search(
            "file_state.last_update_hash"
        ).get_str_or_none()

        if (
            force
            or not hash_protection_active
            or (
                last_update_hash is None
                or repo_has_changed_since(
                    previous_state=last_update_hash, cwd=self.get_path()
                )
            )
        ):
            # Reset hash
            registry.set_by_path("file_state.last_update_hash", None)
            registry_file.write_config()

            result = super().apply(
                scopes=scopes,
                filter_path=filter_path,
                filter_operation=filter_operation,
                max=max,
                **kwargs,
            )

            # Save hash only if protection is active
            if hash_protection_active:
                registry.set_by_path(
                    "file_state.last_update_hash", repo_get_state(cwd=self.get_path())
                )
                registry_file.write_config()

            return result

        self.log("No change since last pass, skipping.", indentation=1)
        return FileStateResult(state_manager=self)

    def bump(self, interactive: bool = False, force: bool = False, **kwargs) -> bool:
        """Create a version-x.y.z branch, update the version number in config. Don't commit changes."""
        from wexample_helpers.helpers.version import version_increment
        from wexample_prompt.responses.interactive.confirm_prompt_response import (
            ConfirmPromptResponse,
        )

        has_changes = self.has_changes_since_last_publication_tag()
        if not force and has_changes:
            self.log(f"Package {self.get_package_name()} has no new content to bump.")
            return False

        current_version = self.get_project_version()
        new_version = version_increment(version=current_version, **kwargs)
        branch_name = f"version-{new_version}"

        self.info(f"Bumping version to {new_version}", prefix=True)

        def _bump() -> None:
            from wexample_helpers_git.helpers.git import git_create_or_switch_branch

            # Create or switch to branch first, so changes are committed on it.
            git_create_or_switch_branch(
                branch_name, cwd=self.get_path(), inherit_stdio=True
            )
            self.log(message=f'Switched to branch "{branch_name}"', indentation=1)

            # Change version number on this branch
            self.write_config_value("global.version", new_version)

            self.log(
                message=f'Bumped from "{current_version}" to "{new_version}"',
                indentation=1,
            )

        if interactive:
            changes_message = (
                " The project contains changes since last publication."
                if has_changes
                else ""
            )

            confirm = self.confirm(
                f"Do you want to create a new version for package {self.get_package_name()} in @path{{{self.get_path()}}}?{changes_message} "
                f'This will create/switch to branch "{branch_name}".',
                choices=ConfirmPromptResponse.MAPPING_PRESET_YES_NO,
                default="yes",
            )

            if confirm.is_ok():
                _bump()
                return True
        else:
            _bump()
            return True
        return False

    def configure(self, config: DictConfig) -> None:
        super().configure(config=config)

        self._init_env(env_dict=self.get_env_parameters().to_dict())

    def count_source_code_lines(self) -> int:
        """Count total lines in source code files."""
        return self._count_code_lines(directories=self._get_source_code_directories())

    def count_source_files(self) -> int:
        """Count number of source code files."""
        return self._count_files(directories=self._get_source_code_directories())

    def count_test_code_lines(self) -> int:
        """Count total lines in test code files."""
        return self._count_code_lines(directories=self._get_test_code_directories())

    def count_test_files(self) -> int:
        """Count number of test code files."""
        return self._count_files(directories=self._get_test_code_directories())

    def ensure_app_manager(self) -> bool:
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

        current_app_manager_path = self.get_path() / APP_PATH_BIN_APP_MANAGER

        if current_app_manager_path.exists():
            return True

        closest_app_manager_path = self.search_closest_app_manager_bin_path()
        if closest_app_manager_path != current_app_manager_path:
            self.log(f"Creating symlink: {current_app_manager_path}")

            # Remove if symlink already exists but point to a missing file.
            current_app_manager_path.unlink()
            current_app_manager_path.symlink_to(closest_app_manager_path.resolve())
            # False says newly created.
            return False
        return True

    def ensure_app_manager_setup(self) -> None:
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

        self._override_pyproject_dependencies_by_current_distribution_versions()
        self.ensure_app_manager()

        self.shell_run_for_app(cmd=[str(APP_PATH_BIN_APP_MANAGER), "setup"])

    def get_app_env(self) -> str:
        from wexample_app.const.globals import ENV_VAR_NAME_APP_ENV

        return self.get_env_parameter(key=ENV_VAR_NAME_APP_ENV, default=ENV_NAME_PROD)

    def get_dependencies_versions(self) -> dict[str, str]:
        return {}

    def get_last_publication_tag(self) -> str | None:
        """Return the last publication tag for this package, or None if none exists."""
        from wexample_helpers_git.helpers.git import git_last_tag_for_prefix

        prefix = f"{self.get_package_name()}/v*"
        return git_last_tag_for_prefix(prefix, cwd=self.get_path(), inherit_stdio=False)

    def get_local_libraries_paths(self) -> list[ConfigValue]:
        return self.get_runtime_config().search(f"libraries").get_list_or_default()

    @abstract_method
    def get_package_import_name(self) -> str:
        pass

    @abstract_method
    def get_main_code_file_extension(self) -> str:
        pass

    def get_package_name(self) -> str:
        return self.get_project_name()

    # Publication helpers
    def get_publication_tag_name(self) -> str:
        """Return the conventional tag name for this package publication.

        Format: "{package_name}/v{version}"
        """
        return f"{self.get_package_name()}/v{self.get_project_version()}"

    def has_a_test(self) -> bool:
        test_dir = self.find_by_name(APP_PATH_TEST)
        return (
            test_dir
            and test_dir.is_directory()
            and any(test_dir.get_path().rglob("*.py"))
        )

    def has_changes_since_last_coverage(self) -> bool:
        """Return True if there are any changes (committed or not) since last coverage."""
        from wexample_helpers_git.helpers.git import git_has_uncommitted_changes

        last_commit = (
            self.get_config()
            .search("test.coverage.last_report.commit_hash")
            .get_str_or_default()
        )

        if not last_commit:
            return True

        return git_has_uncommitted_changes(
            cwd=self.get_path()
        ) or git_has_changes_since_tag(last_commit, cwd=self.get_path())

    def has_changes_since_last_publication_tag(self) -> bool:
        """Return True if there are changes in the package directory since the last publication tag.

        If there is no previous tag, returns True (first publication).
        """
        from wexample_helpers_git.helpers.git import git_has_changes_since_tag

        last_tag = self.get_last_publication_tag()
        if last_tag is None:
            return True
        # Limit diff to current package folder, run from package cwd using '.'
        return git_has_changes_since_tag(last_tag, ".", cwd=self.get_path())

    def libraries_sync(self) -> None:
        from wexample_wex_addon_app.commands.dependencies.publish import (
            app__dependencies__publish,
        )

        for library_path_config in (
            self.get_runtime_config().search("libraries").get_list_or_default()
        ):
            if library_path_config.is_str() and BasicAppWorkdir.is_app_workdir_path(
                path=library_path_config.get_str()
            ):
                publishable_dependencies = (
                    BasicAppWorkdir.manager_run_command_from_path(
                        command=app__dependencies__publish,
                        path=library_path_config.get_str(),
                    ).get_output()
                )

                self.update_dependencies(publishable_dependencies)
        self.io.success("All libraries versions are up to date.")

    def publish(self, force: bool = False) -> None:
        from wexample_helpers_git.const.common import GIT_BRANCH_MAIN

        if not self.should_be_published(force=force):
            return

        self._publish(force=force)
        self.success(
            f"Published {self.get_package_name()} as {self.get_publication_tag_name()}."
        )
        self.add_publication_tag()
        self.merge_to_main()
        self.push_to_deployment_remote(branch_name=GIT_BRANCH_MAIN)

    def publish_bumped(self, force: bool = False, interactive: bool = True) -> None:
        from wexample_wex_addon_app.commands.file_state.rectify import (
            app__file_state__rectify,
        )
        from wexample_wex_addon_app.commands.package.bump import app__package__bump
        from wexample_wex_addon_app.commands.package.commit_and_push import (
            app__package__commit_and_push,
        )
        from wexample_wex_addon_app.commands.package.publish import (
            app__package__publish,
        )
        from wexample_wex_addon_app.commands.version.propagate import (
            app__version__propagate,
        )

        if force or self.has_changes_since_last_publication_tag():
            # Reserve 1 unit on main progress bar, subdivided into 5 steps
            sub_progress = self.progress(
                total=5,
                color=TerminalColor.YELLOW,
                indentation=1,
                print_response=False,
            ).get_handle()

            sub_progress.advance(step=1, label=f"Bumping {self.get_project_name()}")
            bump_args = []
            if force:
                bump_args.append("--force")
            if not interactive:
                bump_args.append("--yes")
            bump_response = self.manager_run_command(
                command=app__package__bump, arguments=bump_args
            ).get_output_value()

            # Bump cancelled.
            if not bump_response.is_true():
                return

            sub_progress.advance(
                step=1, label=f"Rectifying file state for {self.get_project_name()}"
            )
            rectify_args = ["--loop"]
            if not interactive:
                rectify_args.append("--yes")
            self.manager_run_command(
                command=app__file_state__rectify, arguments=rectify_args
            )

            # TODO run tests

            sub_progress.advance(
                step=1, label=f"Committing and pushing {self.get_project_name()}"
            )
            self.manager_run_command(command=app__package__commit_and_push)

            sub_progress.advance(
                step=1, label=f"Propagating version for {self.get_project_name()}"
            )
            self.manager_run_command(command=app__version__propagate)

            sub_progress.advance(step=1, label=f"Publishing {self.get_project_name()}")
            self.manager_run_command(
                command=app__package__publish, arguments=(["--force"] if force else [])
            )
        else:
            self.io.log("No change to publish, skipping.")

    def publish_dependencies(self) -> dict[str, str]:
        """Publish witch dependency **current package represents for others**,
        not the dependencies the current package is dependent on.
        """
        return {self.get_package_name(): self.get_project_version()}

    def search_app_or_suite_runtime_config(
        self, key_path: str, default: Any = None
    ) -> ConfigValue:
        def _test_path(workdir) -> Path | None:
            config = workdir.get_runtime_config().search(path=key_path)
            if not config.is_none():
                return config
            return None

        return self.search_closest_in_suites_tree(callback=_test_path) or ConfigValue(
            raw=default
        )

    def search_closest_app_manager_bin_path(self) -> Path | None:
        def _test_path(workdir) -> Path | None:
            from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

            manager_bin_path = workdir.get_path() / APP_PATH_BIN_APP_MANAGER

            if manager_bin_path.exists():
                return manager_bin_path

        return self.search_closest_in_suites_tree(callback=_test_path)

    def set_app_env(self, env: str | None) -> None:
        from wexample_app.const.globals import ENV_VAR_NAME_APP_ENV

        self.set_env_parameter(key=ENV_VAR_NAME_APP_ENV, value=env)

        self.get_registry(rebuild=True)

    def setup_install(self, env: str | None = None, force: bool = False) -> None:
        env = env or self.get_app_env()
        self.log(f"Set app environment to @🔵+bold{{{env}}}...")
        self.set_app_env(env=env)

        self.log("Check manager setup...")
        self.ensure_app_manager_setup()

        self.log("Install app...")
        self.app_install(env, force=force)

    def should_be_published(self, force: bool = False) -> bool:
        current_tag = self.get_publication_tag_name()
        last_tag = self.get_last_publication_tag()
        if not force and last_tag == current_tag:
            self.log(f"{self.get_package_name()} already published as {current_tag}.")
            return False
        return True

    def update_dependencies(self, dependencies_map: dict[str, str]) -> None:
        # Let language specific workdir manage how to update.
        pass

    def _count_code_lines(
        self,
        directories: list[TargetFileOrDirectoryType],
    ) -> int:
        """Count total lines in files matching the main code extension."""
        total = 0

        for item in directories:
            total += line_count_recursive(
                path=item.get_path(), pattern=f"*{self.get_main_code_file_extension()}"
            )

        return total

    def _count_files(
        self,
        directories: list[TargetFileOrDirectoryType],
    ) -> int:
        """Count files matching the main code extension in given directories."""
        total = 0
        extension = self.get_main_code_file_extension()

        for item in directories:
            path = item.get_path()
            if path.exists() and path.is_dir():
                # Count files with the main code extension
                total += len(list(path.rglob(f"*{extension}")))

        return total

    def _get_source_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _get_suite_package_workdir_class(self) -> type[FrameworkPackageSuiteWorkdir]:
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        """ A suite can be a sub-suite"""
        return FrameworkPackageSuiteWorkdir

    def _get_test_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _override_pyproject_dependencies_by_current_distribution_versions(self) -> None:
        from pathlib import Path

        import tomlkit
        from wexample_helpers.helpers.module import module_get_distribution_map

        installed = module_get_distribution_map()

        manager_path = self.get_path() / APP_PATH_APP_MANAGER
        pyproject_path = Path(manager_path / "pyproject.toml")

        # Read raw text for tomlkit (to preserve comments)
        raw = pyproject_path.read_text()

        # Parse with tomlkit
        doc = tomlkit.parse(raw)

        # "project.dependencies" is a TOML array with preserved formatting
        deps = doc.get("project", {}).get("dependencies", [])

        updated = False
        new_deps = tomlkit.array().multiline(True)

        for dep in deps:
            dep_str = str(dep)

            # Parse dependency into (name, version)
            if "==" in dep_str:
                name, _ = dep_str.split("==", 1)
            elif ">=" in dep_str:
                name, _ = dep_str.split(">=", 1)
            elif "<=" in dep_str:
                name, _ = dep_str.split("<=", 1)
            else:
                # keep untouched (no version specified)
                new_deps.append(dep)
                continue

            pkg_name = name.strip().lower()
            installed_version = installed.get(pkg_name)

            if installed_version:
                new_dep = f"{pkg_name}=={installed_version}"
                if dep_str != new_dep:
                    self.log(f"{dep_str} → {new_dep}")
                    updated = True
                new_deps.append(new_dep)
            else:
                new_deps.append(dep)

        # If changed, replace the array in the document
        if updated:
            doc["project"]["dependencies"] = new_deps

            # Write back, preserving original formatting + comments
            pyproject_path.write_text(tomlkit.dumps(doc))

            self._python_export_dependencies(path=manager_path)

            self.log("✓ pyproject.toml updated")

    def _publish(self, force: bool = False) -> None:
        """Internal publication process"""

    def _python_export_dependencies(self, path: Path) -> None:
        import sys

        self.shell_run_from_path(
            cmd=[
                f"{sys.prefix}/bin/pip-compile",
                f"{path}/pyproject.toml",
                "--output-file",
                f"{path}/requirements.txt",
            ],
            path=path,
        )
