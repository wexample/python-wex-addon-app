from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.abstract_method import abstract_method

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
            self.io.warning(f"Tag {tag} already exists locally; pushing it.")

        # Push the tag explicitly to the remote to ensure it's published.
        git_push_tag(tag, cwd=cwd, inherit_stdio=True)

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
            git_current_branch,
            git_ensure_upstream,
            git_has_index_changes,
            git_has_working_changes,
            git_pull_rebase_autostash,
        )

        cwd = self.get_path()
        progress = (
            progress
            or self.io.progress(label="Committing changes...", total=3).get_handle()
        )

        git_current_branch(cwd=cwd, inherit_stdio=False)
        git_ensure_upstream(cwd=cwd, default_remote="origin", inherit_stdio=True)
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
        """Check if current package depends on given one."""
        return False

    @abstract_method
    def get_dependencies(self) -> list[str]:
        pass

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

    def get_package_name(self) -> str:
        return self.get_project_name()

    def has_working_changes(self) -> bool:
        from wexample_helpers_git.helpers.git import git_has_working_changes

        return git_has_working_changes(cwd=self.get_path(), inherit_stdio=True)

    def imports_package_in_codebase(self, searched_package: CodeBaseWorkdir) -> bool:
        """Check whether the given package is used in this package's codebase."""
        return False

    def push_changes(
        self,
        progress: ProgressHandle | None = None,
    ) -> None:
        """Push current branch to upstream (following tags), without committing."""
        from wexample_helpers_git.helpers.git import (
            git_current_branch,
            git_ensure_upstream,
            git_push_follow_tags,
        )

        from wexample_wex_addon_app.exception.git_remote_exception import (
            GitRemoteException,
        )

        cwd = self.get_path()
        progress = (
            progress
            or self.io.progress(label="Pushing changes...", total=1).get_handle()
        )

        try:
            branch_name = git_current_branch(cwd=cwd, inherit_stdio=False)
            git_ensure_upstream(cwd=cwd, default_remote="origin", inherit_stdio=True)
            git_push_follow_tags(cwd=cwd, inherit_stdio=True)
            progress.finish(label="Pushed")
        except Exception as e:
            raise GitRemoteException(
                workdir_path=str(cwd),
                package_name=self.get_package_name(),
                operation="push",
                remote_name="origin",
                branch_name=branch_name if "branch_name" in locals() else None,
                cause=e,
            ) from e

    def save_dependency(self, package: CodeBaseWorkdir) -> bool:
        """Register a dependency into the configuration file."""
        return True