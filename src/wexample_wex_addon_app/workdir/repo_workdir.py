from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType

from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir

if TYPE_CHECKING:
    pass


class RepoWorkdir(AppWorkdir):
    def bump(self, interactive: bool = False, force: bool = False, **kwargs) -> bool:
        """Create a version-x.y.z branch, update the version number in config. Don't commit changes."""
        from wexample_helpers.helpers.version import version_increment
        from wexample_prompt.responses.interactive.confirm_prompt_response import (
            ConfirmPromptResponse,
        )

        has_changes = self.has_changes_since_last_publication_tag()
        if not force and not has_changes:
            self.log(f"Package {self.get_package_name()} has no new content to bump.")
            return False

        current_version = self.get_project_version()
        new_version = version_increment(version=current_version, **kwargs)
        branch_name = f"version-{new_version}"

        self.info(f"Bumping version to {new_version}", prefix=True)

        def _bump() -> None:
            from wexample_helpers_git.helpers.git import git_create_or_switch_branch

            git_create_or_switch_branch(
                branch_name, cwd=self.get_path(), inherit_stdio=True
            )
            self.log(message=f'Switched to branch "{branch_name}"', indentation=1)

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

    def count_source_code_lines(self) -> int:
        return self._count_code_lines(self._get_source_code_directories())

    def count_source_files(self) -> int:
        return self._count_files(self._get_source_code_directories())

    def count_test_code_lines(self) -> int:
        return self._count_code_lines(self._get_test_code_directories())

    def count_test_files(self) -> int:
        return self._count_files(self._get_test_code_directories())

    def get_dependencies_versions(self) -> dict[str, str]:
        return {}

    def get_last_publication_tag(self) -> str | None:
        """Return the last publication tag for this package, or None if none exists."""
        from wexample_helpers_git.helpers.git import git_last_tag_for_prefix

        prefix = f"{self.get_package_name()}/v*"
        return git_last_tag_for_prefix(prefix, cwd=self.get_path(), inherit_stdio=False)

    def get_main_code_file_extension(self) -> str | None:
        return None

    def get_package_name(self) -> str:
        return self.get_project_name()

    def get_publication_tag_name(self) -> str:
        """Return the conventional tag name for this package publication.

        Format: "{package_name}/v{version}"
        """
        return f"{self.get_package_name()}/v{self.get_project_version()}"

    def has_a_test(self) -> bool:
        from wexample_wex_addon_app.const.path import APP_PATH_TEST

        test_dir = self.find_by_name(APP_PATH_TEST)
        return (
            test_dir
            and test_dir.is_directory()
            and any(test_dir.get_path().rglob("*.py"))
        )

    def has_changes_since_last_coverage(self) -> bool:
        from wexample_helpers_git.helpers.git import (
            git_has_changes_since_tag,
            git_has_uncommitted_changes,
        )

        last_commit = (
            self.get_config()
            .search("test.coverage.last_report.commit_hash")
            .get_str_or_default()
        )

        if not last_commit:
            return True

        return git_has_uncommitted_changes(
            cwd=self.get_path()
        ) or git_has_changes_since_tag(last_commit, ".", cwd=self.get_path())

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
            if interactive:
                if not self.io.confirm(
                    f"Package {self.get_package_name()} has changes, do you want to publish it?"
                ):
                    return

            bumped = self.bump(interactive=interactive, force=force)

            if not bumped:
                return

            rectify_args = ["--loop"] + (["--yes"] if not interactive else [])
            self.manager_run_command(
                command=app__file_state__rectify, arguments=rectify_args
            )

            self.manager_run_command(command=app__package__commit_and_push)

            self.manager_run_command(command=app__version__propagate)

            self.manager_run_command(
                command=app__package__publish, arguments=["--force"]
            )

    def publish_dependencies(self) -> None:
        pass

    def should_be_published(self, force: bool = False) -> bool:
        return force or self.has_changes_since_last_publication_tag()

    def update_dependencies(self, dependencies_map: dict[str, str]) -> None:
        pass

    def _count_code_lines(self, directories: list[TargetFileOrDirectoryType]) -> int:
        from wexample_file.helper.line import line_count_recursive

        count = 0
        for directory in directories:
            path = self.get_path() / directory
            if path.exists():
                count += line_count_recursive(path)
        return count

    def _count_files(self, directories: list[TargetFileOrDirectoryType]) -> int:
        count = 0
        for directory in directories:
            path = self.get_path() / directory
            if path.exists():
                count += len(list(path.rglob("*")))
        return count

    def _get_source_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _get_test_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _publish(self, force: bool = False) -> None:
        pass
