from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers_git.const.common import GIT_BRANCH_MAIN, GIT_REMOTE_ORIGIN
from wexample_helpers_git.helpers.git import git_run

from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

if TYPE_CHECKING:
    from wexample_config.options_provider.abstract_options_provider import (
        AbstractOptionsProvider,
    )
    from wexample_prompt.common.progress.progress_handle import ProgressHandle


class CodeBaseWorkdir(RepoWorkdir):
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
        git_push_tag(
            tag, cwd=cwd, remote=self._get_deployment_remote_name(), inherit_stdio=True
        )

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

    def commit_propagated_dependency_updates(self) -> None:
        """Commit and push dependency-version updates written by propagate_version.

        Called for packages skipped during suite publication (no real source
        changes) but whose config files (e.g. composer.json) were modified by
        a sibling package's propagate_version step.  Committing here prevents
        those diffs from accumulating as false positives on the next publish run.
        """
        from wexample_helpers_git.const.common import GIT_BRANCH_MAIN
        from wexample_helpers_git.helpers.git import (
            git_commit_all_with_message,
            git_has_uncommitted_changes,
        )

        cwd = self.get_path()
        if not git_has_uncommitted_changes(cwd=cwd):
            return

        self.log(
            f"Committing propagated dependency updates for {self.get_package_name()}",
            prefix=True,
        )
        git_commit_all_with_message(
            "Update dependency versions",
            cwd=cwd,
            inherit_stdio=True,
        )
        self.push_to_deployment_remote(branch_name=GIT_BRANCH_MAIN)

    def depends_from(self, package: CodeBaseWorkdir) -> bool:
        for dependence_name in self.get_dependencies_versions().keys():
            if package.get_package_dependency_name() == dependence_name:
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

    def get_package_dependency_name(self) -> str:
        """Return the name used by other packages to mark it as a dependency"""
        return self.get_package_name()

    def git_run(self, *args, **kwargs):
        return git_run(
            cwd=self.get_path(),
            *args,
            **kwargs,
        )

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

    def push_changes(
        self,
        remote_name: str | None = None,
        branch_name: str | None = None,
    ) -> None:
        from wexample_helpers_git.helpers.git import git_current_branch
        from wexample_helpers_git.helpers.git_retryable_callback_manager import (
            GitRetryableCallbackManager,
        )

        remote = remote_name or GIT_REMOTE_ORIGIN
        if branch_name is None:
            branch_name = git_current_branch(cwd=self.get_path(), inherit_stdio=False)

        local_branch, remote_branch = (
            branch_name.split(":", 1)
            if ":" in branch_name
            else (branch_name, branch_name)
        )

        def _run_push() -> None:
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

        def _on_retry(
            attempt: int,
            max_attempts: int,
            delay_seconds: int,
            exc: Exception,
            message: str,
        ) -> None:
            self.warning(
                f"git push failed (attempt {attempt}/{max_attempts}); retrying in {delay_seconds}s."
            )

        def _on_error(exc: Exception, message: str) -> None:
            stderr = getattr(exc, "stderr", None)
            stdout = getattr(exc, "stdout", None)
            if stderr:
                self.error(f"git push stderr:\n{stderr.strip()}")
            if stdout:
                self.error(f"git push stdout:\n{stdout.strip()}")

        GitRetryableCallbackManager(
            callback=_run_push,
            max_attempts=3,
            on_retry_callback=_on_retry,
            on_error_callback=_on_error,
        ).run()

    def push_to_deployment_remote(self, branch_name: str | None = None) -> None:
        self.push_changes(
            remote_name=self._get_deployment_remote_name(),
            branch_name=branch_name,
        )

    def save_dependency(self, package: str, version: str, operator: str = ">=") -> bool:
        """Add or update a dependency constraint."""
        config = self.get_app_config_file()
        return config.add_dependency(
            package=package, version=version, operator=operator
        )

    def update_dependencies(self, dependencies_map: dict[str, str]) -> None:
        """Update dependencies versions based on the provided map.

        Args:
            dependencies_map: Dictionary mapping package names to their new versions.
                             Example: {"wexample-helpers": "0.2.3", "attrs": "23.1.0"}
        """
        from packaging.utils import canonicalize_name

        config_file = self.get_app_config_file()

        # Canonicalize the keys in dependencies_map for consistent matching
        canonical_map = {
            canonicalize_name(name): version
            for name, version in dependencies_map.items()
        }

        current_deps = config_file.get_dependencies_versions()

        # Update each dependency if it's in the map
        for dep_name, dep_version in current_deps.items():
            canonical_name = canonicalize_name(dep_name)

            if canonical_name in canonical_map:
                new_version = canonical_map[canonical_name]
                config_file.add_dependency_from_string(
                    package_name=dep_name, version=new_version
                )

        # Save the updated config
        config_file.write_parsed()

    def _build_dependency_string(self, package_name: str, version: str) -> str:
        return f"{package_name}=={version}"

    def _get_critical_directories(self) -> list[str]:
        return []

    def _get_deployment_remote_name(self) -> str | None:
        from wexample_helpers_git.const.common import GIT_REMOTE_ORIGIN

        return self.search_app_or_suite_runtime_config(
            "git.main_deployment_remote_name", default=GIT_REMOTE_ORIGIN
        ).get_str_or_none()
