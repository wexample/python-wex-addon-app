from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers_git.const.common import GIT_BRANCH_MAIN, GIT_REMOTE_ORIGIN
from wexample_helpers_git.helpers.git import git_run
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_config.options_provider.abstract_options_provider import (
        AbstractOptionsProvider,
    )
    from wexample_prompt.common.progress.progress_handle import ProgressHandle


class CodeBaseWorkdir(BasicAppWorkdir):
    def add_publication_tag(self) -> None:
        from wexample_helpers_git.helpers.git import (
            git_push_tag,
            git_tag_annotated,
            git_tag_exists,
        )

        cwd = self.get_path()
        tag = f"{self.get_package_name()}/v{self.get_project_version()}"

        # Create the annotated tag if it does not already exist locally.
        if not git_tag_exists(tag, cwd=cwd, inherit_stdio=False):
            git_tag_annotated(tag, f"Release {tag}", cwd=cwd, inherit_stdio=True)
        else:
            self.warning(f"Tag {tag} already exists locally; pushing it.")

        # Push the tag explicitly to the remote to ensure it's published.
        git_push_tag(tag, cwd=cwd, inherit_stdio=True)

    def _build_dependency_string(self, package_name: str, version: str) -> str:
        return f"{package_name}=={version}"

    def build_dependencies_stack(
        self, package: CodeBaseWorkdir, dependency: CodeBaseWorkdir
    ) -> list[CodeBaseWorkdir]:
        """When package is dependent from another one (is using it in its codebase),
        list the packages inheritance stack to find the original package declaring the explicit dependency
        """
        return []

    def commit_changes(
        self,
        progress: ProgressHandle | None = None,
    ) -> None:
        """Commit local changes (if any), without pushing."""
        from wexample_helpers_git.helpers.git import (
            git_commit_all_with_message,
            git_ensure_upstream,
            git_has_index_changes,
            git_has_working_changes,
            git_pull_rebase_autostash,
        )

        cwd = self.get_path()
        progress = (
            progress
            or self.progress(label="Committing changes...", total=3).get_handle()
        )

        git_ensure_upstream(
            cwd=cwd,
            default_remote=self._get_deployment_remote_name(),
            inherit_stdio=True,
        )
        progress.advance(step=1, label="Ensured upstream")

        git_pull_rebase_autostash(cwd=cwd, inherit_stdio=True)
        progress.advance(step=1, label="Pulled latest (rebase)")

        has_working_changes = git_has_working_changes(cwd=cwd)
        has_index_changes = git_has_index_changes(cwd=cwd)

        if has_working_changes or has_index_changes:
            git_commit_all_with_message(
                f"Publishing version {self.get_project_version()}",
                cwd=cwd,
                inherit_stdio=True,
            )
            progress.finish(label="Committed changes")
        else:
            progress.finish(label="No changes to commit")

    def depends_from(self, package: CodeBaseWorkdir) -> bool:
        for dependence_name in self.get_dependencies_versions().keys():
            if package.get_package_name() == dependence_name:
                return True
        return False

    def get_io_context_prefix(self) -> str | None:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        """Get the prefix to prepend to messages (e.g., '[child]')."""
        return cli_make_clickable_path(self.get_path(), self.get_project_name())

    def get_io_context_prefix_format(self) -> str:
        return "‹› {prefix} | "

    def get_options_providers(self) -> list[type[AbstractOptionsProvider]]:
        from wexample_filestate.options_provider.default_options_provider import (
            DefaultOptionsProvider,
        )
        from wexample_filestate_git.options_provider.git_options_provider import (
            GitOptionsProvider,
        )

        return [
            DefaultOptionsProvider,
            GitOptionsProvider,
        ]

    def has_working_changes(self) -> bool:
        from wexample_helpers_git.helpers.git import git_has_working_changes

        return git_has_working_changes(cwd=self.get_path(), inherit_stdio=True)

    def imports_package_in_codebase(self, searched_package: CodeBaseWorkdir) -> bool:
        """Check whether the given package is used in this package's codebase."""
        return False

    def merge_to_main(self, branch_name: str = GIT_BRANCH_MAIN) -> None:
        """Merge current branch into the specified main branch, then return to the original branch.

        :param branch_name: Name of the main branch (default: "main").

        This method:
        1. Saves the current branch name
        2. Merges main into the current branch (to ensure compatibility)
        3. Switches to the main branch
        4. Merges the current branch into main
        5. Returns to the original branch

        Raises if there are uncommitted changes or merge conflicts.
        """
        from wexample_helpers.helpers.shell import shell_run
        from wexample_helpers_git.helpers.git import (
            git_current_branch,
            git_has_uncommitted_changes,
            git_switch_branch,
        )

        cwd = self.get_path()

        # Ensure no uncommitted changes before starting
        if git_has_uncommitted_changes(cwd=cwd):
            raise RuntimeError(
                f"Cannot merge to {branch_name}: uncommitted changes detected. "
                "Please commit or stash your changes first."
            )

        # Save current branch name
        current_branch = git_current_branch(cwd=cwd, inherit_stdio=False)

        if current_branch == branch_name:
            self.warning(f"Already on {branch_name} branch, nothing to merge.")
            return

        try:
            # Step 1: Merge main into current branch to ensure compatibility
            self.info(f"Merging {branch_name} into {current_branch}...")
            shell_run(
                [
                    "git",
                    "merge",
                    branch_name,
                    "--no-ff",
                    "-m",
                    f"Merge branch '{branch_name}' into {current_branch}",
                ],
                inherit_stdio=True,
                cwd=cwd,
            )

            # Step 2: Switch to main
            self.info(f"Switching to {branch_name}...")
            git_switch_branch(branch_name, cwd=cwd, inherit_stdio=True)

            # Step 3: Merge current branch into main
            self.info(f"Merging {current_branch} into {branch_name}...")
            shell_run(
                [
                    "git",
                    "merge",
                    current_branch,
                    "--no-ff",
                    "-m",
                    f"Merge branch '{current_branch}' into {branch_name}",
                ],
                inherit_stdio=True,
                cwd=cwd,
            )

            self.success(f"Successfully merged {current_branch} into {branch_name}")

        finally:
            # Step 4: Always return to the original branch
            self.info(f"Returning to {current_branch}...")
            git_switch_branch(current_branch, cwd=cwd, inherit_stdio=True)

    def _get_deployment_remote_name(self) -> str | None:
        return self.search_app_or_suite_runtime_config(
            "git.main_deployment_remote_name", default=None
        ).get_str_or_none()

    def push_to_deployment_remote(self, branch_name: str | None = None) -> None:
        self.push_changes(
            remote_name=self._get_deployment_remote_name(),
            branch_name=branch_name,
        )

    def push_changes(
        self,
        remote_name: str | None = None,
        branch_name: str | None = None,
    ) -> None:
        remote = remote_name or GIT_REMOTE_ORIGIN
        branch_name = branch_name or GIT_BRANCH_MAIN

        local_branch, remote_branch = (
            branch_name.split(":", 1)
            if ":" in branch_name
            else (branch_name, branch_name)
        )

        self.git_run(
            cmd=[
                "push",
                remote,
                f"{local_branch}:{remote_branch}",
                "--follow-tags",
                "--force",
                "--porcelain",
            ],
            inherit_stdio=False,
        )

    def git_run(self, *args, **kwargs):
        return git_run(
            cwd=self.get_path(),
            *args,
            **kwargs,
        )

    def save_dependency(self, package_name: str, version: str) -> bool:
        """Add or update a dependency with strict version."""
        config = self.get_app_config_file()
        return config.add_dependency(package_name=package_name, version=version)
