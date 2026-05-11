from __future__ import annotations

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)


class BranchMergePublicationStrategy(AbstractPublicationStrategy):
    """Branch-then-merge workflow.

    Temporary: delete+repush tag to force GitLab CI trigger on the branch commit.
    Will be replaced in Phase 3 by full MR creation + CI polling.
    """

    def wait_for_ci(self) -> None:
        from wexample_helpers.helpers.shell import shell_run
        from wexample_helpers_git.helpers.git import git_push_tag

        tag = f"v{self.workdir.get_project_version()}"
        cwd = self.workdir.get_path()
        remote = self.workdir._get_deployment_remote_name() or "origin"

        self.workdir.log(f"Re-pushing tag {tag} to force CI trigger…")

        shell_run(
            ["git", "push", remote, f":refs/tags/{tag}"],
            cwd=cwd,
            inherit_stdio=True,
            check=False,
        )
        git_push_tag(tag, cwd=cwd, remote=remote, inherit_stdio=True)
