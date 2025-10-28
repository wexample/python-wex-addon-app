from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin
from wexample_wex_core.workdir.workdir import Workdir

if TYPE_CHECKING:
    from wexample_filestate.result.file_state_result import FileStateResult


@base_class
class BasicAppWorkdir(AppWorkdirMixin, Workdir):
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

        self.io.log("No change since last pass, skipping.", indentation=1)
        return FileStateResult(state_manager=self)

    def bump(self, interactive: bool = False, **kwargs) -> bool:
        """Create a version-x.y.z branch, update the version number in config. Don't commit changes."""
        from wexample_helpers.helpers.version import version_increment
        from wexample_prompt.responses.interactive.confirm_prompt_response import (
            ConfirmPromptResponse,
        )

        current_version = self.get_project_version()
        new_version = version_increment(version=current_version, **kwargs)
        branch_name = f"version-{new_version}"

        def _bump() -> None:
            from wexample_helpers_git.helpers.git import git_create_or_switch_branch

            # Create or switch to branch first, so changes are committed on it.
            git_create_or_switch_branch(
                branch_name, cwd=self.get_path(), inherit_stdio=True
            )

            # Change version number on this branch
            self.get_config_file().write_config_value("global.version", new_version)

            self.success(
                f'Bumped {self.get_package_name()} from "{current_version}" to "{new_version}" and switched to branch "{branch_name}"'
            )

        if interactive:

            confirm = self.confirm(
                f"Do you want to create a new version for package {self.get_package_name()} in {self.get_path()}? "
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

    def get_last_publication_tag(self) -> str | None:
        """Return the last publication tag for this package, or None if none exists."""
        from wexample_helpers_git.helpers.git import git_last_tag_for_prefix

        prefix = f"{self.get_package_name()}/v*"
        return git_last_tag_for_prefix(prefix, cwd=self.get_path(), inherit_stdio=False)

    def get_package_name(self) -> str:
        return self.get_item_name()

    # Publication helpers
    def get_publication_tag_name(self) -> str:
        """Return the conventional tag name for this package publication.

        Format: "{package_name}/v{version}"
        """
        return f"{self.get_package_name()}/v{self.get_project_version()}"

    def has_changes_since_last_publication_tag(self) -> bool:
        """Return True if there are changes in the package directory since the last publication tag.

        If there is no previous tag, returns True (first publication).
        """
        from wexample_helpers_git.helpers.git import git_has_changes_since_tag

        last_tag = self.get_last_publication_tag()
        if last_tag is None:
            return True
        # Limit diff to current package folder, run from package cwd using '.'
        return git_has_changes_since_tag(
            last_tag, ".", cwd=self.get_path(), inherit_stdio=False
        )

    def setup_install(self, env: str | None = None) -> None:
        from wexample_app.const.env import ENV_NAME_LOCAL

        package_name = self.get_path().name
        env_label = f" ({env})" if env else ""

        self.io.log(f"Installing dependencies for {package_name}{env_label}")
        self.shell_run_from_path(path=self.get_path(), cmd=self._create_setup_command())

        if env == ENV_NAME_LOCAL:
            from wexample_app.const.globals import APP_PATH_APP_MANAGER

            suite_workdir = self.get_suite_workdir()
            if suite_workdir:
                app_path = self.get_path()
                packages = suite_workdir.get_ordered_packages()

                self.io.log(
                    f"Installing {len(packages)} local suite packages in editable mode",
                    indentation=1,
                )

                # Install every local package of the suite in editable mode
                for package in packages:
                    package_path = package.get_path()

                    self.io.log(f"Installing {package_path.name}", indentation=2)

                    self.shell_run_from_path(
                        path=app_path / APP_PATH_APP_MANAGER,
                        cmd=[
                            ".venv/bin/python",
                            "-m",
                            "pip",
                            "install",
                            "-e",
                            str(package_path),
                        ],
                    )

    def _create_setup_command(self) -> list[str]:
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

        return [str(APP_PATH_BIN_APP_MANAGER), "setup"]

    def get_local_libraries_paths(self, env: str | None = None) -> list[Path]:
        """Get local library paths from config with environment variable resolution.

        Args:
            env: Environment name (e.g., 'local', 'prod'). If None, uses current environment.

        Returns:
            List of resolved absolute paths to local libraries.
        """
        from wexample_app.const.env import ENV_NAME_LOCAL

        if env is None:
            env = ENV_NAME_LOCAL

        # Get libraries from config: env.{env}.libraries
        libraries_config = (
            self.get_config().search(f"env.{env}.libraries").get_list_or_none()
        )

        if not libraries_config:
            return []

        resolved_paths: list[Path] = []

        for lib_config in libraries_config:
            lib_path_str = lib_config.get_str()

            # Resolve environment variables (e.g., ${LOCAL_WEXAMPLE_PIP_SUITE_PATH})
            lib_path_str = os.path.expandvars(lib_path_str)

            # Convert to absolute path
            lib_path = Path(lib_path_str)
            if not lib_path.is_absolute():
                lib_path = self.get_path() / lib_path

            # Only add if path exists
            if lib_path.exists():
                resolved_paths.append(lib_path.resolve())

        return resolved_paths
